"""Round trip of the RabbitMQ and Redis state of a universe through a snapshot, against real services."""

import asyncio
import datetime

import aio_pika
import pytest
import redis

from ostorlab.runtimes.local import snapshot
from ostorlab.runtimes.local import snapshot_state

MQ_URL = "amqp://guest:guest@localhost:5672/"
MQ_MANAGEMENT_URL = "http://guest:guest@localhost:15672/"
REDIS_URL = "redis://localhost:6379/0"
EXCHANGE = "snapshot_test_exchange"
QUEUE = "snapshot_test_queue"
AGENT_KEY = b"snapshot_test:agent"
TTL_KEY = b"snapshot_test:ttl"
RUN_KEY = b"ostorlab:run:snapshot_test"
TIMESTAMP = datetime.datetime(2026, 1, 12, 12, 0, tzinfo=datetime.timezone.utc)
HEADERS = {
    "trace": bytearray(b"\x01\x02"),
    "retried": True,
    "attempts": 2,
    "chain": ["a", 1],
    "nested": {"depth": 1},
}


async def _set_up_queues() -> None:
    async with await aio_pika.connect(MQ_URL) as connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            EXCHANGE, type=aio_pika.ExchangeType.TOPIC, durable=True
        )
        queue = await channel.declare_queue(
            QUEUE, durable=True, arguments={"x-max-priority": 10}
        )
        await queue.bind(exchange, routing_key="v3.asset.ip.#")
        # Bindings of the built-in amq.* exchanges are not captured, RabbitMQ recreates the exchanges.
        await queue.bind("amq.topic", routing_key="v3.#")
        await exchange.publish(
            aio_pika.Message(
                body=b"\x0a\x04\x08\x08\x08\x08",
                headers=HEADERS,
                priority=5,
                expiration=600,
                timestamp=TIMESTAMP,
                reply_to="nmap_replies",
                message_id="m-1",
            ),
            routing_key="v3.asset.ip.v4",
        )
        await exchange.publish(
            aio_pika.Message(body=b"low priority", priority=1),
            routing_key="v3.asset.ip.v6",
        )


async def _delete_queues() -> None:
    async with await aio_pika.connect(MQ_URL) as connection:
        channel = await connection.channel()
        await channel.queue_delete(QUEUE)
        await channel.exchange_delete(EXCHANGE)


async def _message_count() -> int:
    async with await aio_pika.connect(MQ_URL) as connection:
        channel = await connection.channel()
        queue = await channel.declare_queue(QUEUE, passive=True)
        return queue.declaration_result.message_count


async def _pending_messages() -> list[aio_pika.abc.AbstractIncomingMessage]:
    async with await aio_pika.connect(MQ_URL) as connection:
        channel = await connection.channel()
        queue = await channel.declare_queue(QUEUE, passive=True)
        messages = []
        while (message := await queue.get(no_ack=True, fail=False)) is not None:
            messages.append(message)
        return messages


async def _publish_to_exchange(routing_key: str) -> None:
    async with await aio_pika.connect(MQ_URL) as connection:
        channel = await connection.channel()
        exchange = await channel.get_exchange(EXCHANGE)
        await exchange.publish(aio_pika.Message(body=b"new"), routing_key=routing_key)


async def _restore_exchange_exists() -> bool:
    async with await aio_pika.connect(MQ_URL) as connection:
        channel = await connection.channel()
        try:
            await channel.get_exchange(snapshot_state.RESTORE_EXCHANGE)
        except aio_pika.exceptions.ChannelNotFoundEntity:
            return False
        return True


def _test_part(universe_snapshot: snapshot.Snapshot) -> snapshot.Snapshot:
    """Keep the items created by the test: the services are shared with other tests."""
    proto = universe_snapshot.proto
    queues = [queue for queue in proto.queues if queue.name == QUEUE]
    exchanges = [exchange for exchange in proto.exchanges if exchange.name == EXCHANGE]
    keys = [key for key in proto.redis_keys if key.key.startswith(b"snapshot_test:")]
    del proto.queues[:]
    proto.queues.extend(queues)
    del proto.exchanges[:]
    proto.exchanges.extend(exchanges)
    del proto.redis_keys[:]
    proto.redis_keys.extend(keys)
    return universe_snapshot


@pytest.mark.docker
def testSnapshotState_whenTakenThenRestored_bringsBackQueuesMessagesAndRedisState(
    mq_service, redis_service
) -> None:
    del mq_service, redis_service
    asyncio.run(_set_up_queues())
    redis_client = redis.Redis.from_url(REDIS_URL)
    redis_client.set(AGENT_KEY, b"tested")
    redis_client.set(TTL_KEY, b"short lived", ex=1000)
    redis_client.set(RUN_KEY, b"tracker clock")
    try:
        universe_snapshot = snapshot_state.take_snapshot(
            universe="42",
            mq_url=MQ_URL,
            mq_management_url=MQ_MANAGEMENT_URL,
            mq_vhost="/",
            redis_url=REDIS_URL,
        )

        # Taking the snapshot leaves the messages in their queue.
        assert asyncio.run(_message_count()) == 2
        assert RUN_KEY not in [key.key for key in universe_snapshot.proto.redis_keys]
        captured_queue = next(
            queue for queue in universe_snapshot.proto.queues if queue.name == QUEUE
        )
        assert [binding.exchange for binding in captured_queue.bindings] == [EXCHANGE]

        restored_from = snapshot.Snapshot.from_bytes(
            _test_part(universe_snapshot).to_bytes()
        )
        asyncio.run(_delete_queues())
        redis_client.delete(AGENT_KEY, TTL_KEY)

        snapshot_state.restore_snapshot(
            restored_from, mq_url=MQ_URL, redis_url=REDIS_URL
        )

        messages = asyncio.run(_pending_messages())
        assert [message.body for message in messages] == [
            b"\x0a\x04\x08\x08\x08\x08",
            b"low priority",
        ]
        restored = messages[0]
        assert restored.routing_key == "v3.asset.ip.v4"
        assert restored.priority == 5
        assert restored.expiration == 600
        assert restored.timestamp == TIMESTAMP
        assert restored.reply_to == "nmap_replies"
        assert restored.message_id == "m-1"
        assert restored.headers == HEADERS | {
            snapshot_state.RESTORE_QUEUE_HEADER: QUEUE
        }
        # The binding is restored: a new message published to the exchange reaches the queue.
        asyncio.run(_publish_to_exchange("v3.asset.ip.v4"))
        assert asyncio.run(_message_count()) == 1
        assert asyncio.run(_restore_exchange_exists()) is False
        assert redis_client.get(AGENT_KEY) == b"tested"
        assert 0 < redis_client.ttl(TTL_KEY) <= 1000
    finally:
        asyncio.run(_delete_queues())
        redis_client.delete(AGENT_KEY, TTL_KEY, RUN_KEY)
        redis_client.close()
