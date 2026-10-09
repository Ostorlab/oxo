"""Take and restore the RabbitMQ and Redis state of a scan universe, used to pause and resume scans.

The stop scan agent takes the snapshot from inside the universe network once the agents are stopped, and the restore
container runs `main` inside the universe network before the agents of a resumed universe start. Both run from agent
images, so the module relies on the agent requirements (aio-pika, redis).

Messages are restored through a headers exchange matching on `RESTORE_QUEUE_HEADER`, so each message lands in the
queue it was taken from while keeping its original routing key, which agents read as the message selector.
"""

from __future__ import annotations

import argparse
import asyncio
import datetime
import logging
import pathlib
import time
from typing import Any
from urllib import parse

import aio_pika
import httpx
import redis
import tenacity

from ostorlab.runtimes.local import snapshot
from ostorlab.runtimes.local.proto import universe_snapshot_pb2

logger = logging.getLogger(__name__)

RESTORE_EXCHANGE = "ostorlab.snapshot.restore"
# RabbitMQ ignores binding arguments starting with `x-` when matching headers, the header must not use that prefix.
RESTORE_QUEUE_HEADER = "ostorlab-snapshot-restore-queue"

MANAGEMENT_API_TIMEOUT = datetime.timedelta(seconds=30)
# Time to receive the pending messages of a queue, the agents are stopped so the queue does not grow meanwhile.
READ_QUEUE_TIMEOUT = datetime.timedelta(minutes=5)
# A queue delivering nothing for this long is drained: messages counted when it was declared may have expired since.
READ_IDLE_TIMEOUT = datetime.timedelta(seconds=5)
# Messages published concurrently, their publisher confirms are awaited together.
PUBLISH_BATCH_SIZE = 500
RESTORE_ATTEMPTS = 30
RESTORE_RETRY_WAIT = datetime.timedelta(seconds=2)


def take_snapshot(
    universe: str,
    mq_url: str,
    mq_management_url: str,
    mq_vhost: str,
    redis_url: str,
) -> snapshot.Snapshot:
    """Capture the pending messages and the Redis keys of a universe whose agents are stopped.

    Messages are received without acknowledgment and left in their queues, so the universe can resume when the pause
    is rolled back.

    Args:
        universe: Universe identifier.
        mq_url: AMQP URL of the universe RabbitMQ.
        mq_management_url: URL of the universe RabbitMQ management API.
        mq_vhost: RabbitMQ virtual host of the universe.
        redis_url: URL of the universe Redis.

    Returns:
        The universe snapshot.
    """
    # Kept for information: when the scan was paused, the agents being stopped already.
    paused_at_ms = int(time.time() * 1000)
    exchanges, queues = _list_mq_topology(mq_management_url, mq_vhost)
    asyncio.run(_read_queues_messages(mq_url, queues))
    universe_snapshot = snapshot.Snapshot(
        universe_snapshot_pb2.UniverseSnapshot(
            version=snapshot.SNAPSHOT_VERSION,
            universe=universe,
            paused_at_ms=paused_at_ms,
            exchanges=exchanges,
            queues=queues,
            redis_keys=_dump_redis(redis_url),
        )
    )
    logger.info(
        "snapshot of universe %s: %s queues, %s messages, %s redis keys",
        universe,
        len(universe_snapshot.proto.queues),
        universe_snapshot.messages_count,
        len(universe_snapshot.proto.redis_keys),
    )
    return universe_snapshot


def restore_snapshot(
    universe_snapshot: snapshot.Snapshot, mq_url: str, redis_url: str
) -> None:
    """Restore a snapshot in a universe whose agents are not started yet.

    Args:
        universe_snapshot: The snapshot to restore.
        mq_url: AMQP URL of the universe RabbitMQ.
        redis_url: URL of the universe Redis.
    """
    _restore_redis(redis_url, universe_snapshot)
    asyncio.run(_restore_mq(mq_url, universe_snapshot))
    logger.info(
        "restored universe %s: %s queues, %s messages, %s redis keys",
        universe_snapshot.universe,
        len(universe_snapshot.proto.queues),
        universe_snapshot.messages_count,
        len(universe_snapshot.proto.redis_keys),
    )


def _list_mq_topology(
    mq_management_url: str, mq_vhost: str
) -> tuple[list[universe_snapshot_pb2.Exchange], list[universe_snapshot_pb2.Queue]]:
    """List the exchanges and the queues with their bindings using the RabbitMQ management API."""
    vhost = parse.quote(mq_vhost, safe="")
    with httpx.Client(
        base_url=mq_management_url, timeout=MANAGEMENT_API_TIMEOUT.total_seconds()
    ) as client:
        exchanges = [
            universe_snapshot_pb2.Exchange(
                name=exchange["name"],
                type=exchange["type"],
                durable=exchange["durable"],
                auto_delete=exchange["auto_delete"],
                arguments=_to_field_table(exchange.get("arguments") or {}),
            )
            for exchange in _get_json(client, f"api/exchanges/{vhost}")
            if exchange["name"] != "" and exchange["name"].startswith("amq.") is False
        ]
        queues = []
        for queue in _get_json(client, f"api/queues/{vhost}"):
            name = queue["name"]
            bindings = [
                universe_snapshot_pb2.Binding(
                    exchange=binding["source"],
                    routing_key=binding["routing_key"],
                    arguments=_to_field_table(binding.get("arguments") or {}),
                )
                for binding in _get_json(
                    client, f"api/queues/{vhost}/{parse.quote(name, safe='')}/bindings"
                )
                # The default exchange and the excluded amq.* exchanges are not captured, neither are their bindings.
                if binding["source"] != ""
                and binding["source"].startswith("amq.") is False
            ]
            queues.append(
                universe_snapshot_pb2.Queue(
                    name=name,
                    durable=queue["durable"],
                    arguments=_to_field_table(queue.get("arguments") or {}),
                    bindings=bindings,
                )
            )
    return exchanges, queues


def _get_json(client: httpx.Client, path: str) -> list[dict[str, Any]]:
    response = client.get(path)
    response.raise_for_status()
    return response.json()


async def _read_queues_messages(
    mq_url: str, queues: list[universe_snapshot_pb2.Queue]
) -> None:
    """Receive every pending message of the queues with a consumer, without acknowledging them.

    The broker pushes the messages without a per-message round trip. The channel has no prefetch limit since no
    message is acknowledged before every pending message is received. The connection is closed once the messages are
    read, which puts the messages back in their queues.
    """
    connection = await aio_pika.connect(mq_url)
    try:
        channel = await connection.channel()
        for queue in queues:
            mq_queue = await channel.declare_queue(queue.name, passive=True)
            pending = mq_queue.declaration_result.message_count
            if pending == 0:
                continue
            await asyncio.wait_for(
                _receive_messages(mq_queue, queue, pending),
                timeout=READ_QUEUE_TIMEOUT.total_seconds(),
            )
    finally:
        await connection.close()


async def _receive_messages(
    mq_queue: aio_pika.abc.AbstractQueue,
    queue: universe_snapshot_pb2.Queue,
    pending: int,
) -> None:
    """Receive up to `pending` messages, stopping early once the queue is drained.

    A message with a per-message TTL can expire between the declare counting it and its delivery, waiting for the
    declared count would then stall the pause until `READ_QUEUE_TIMEOUT`.
    """
    async with mq_queue.iterator(no_ack=False) as messages:
        while len(queue.messages) < pending:
            try:
                message = await asyncio.wait_for(
                    anext(messages), timeout=READ_IDLE_TIMEOUT.total_seconds()
                )
            except TimeoutError:
                return
            queue.messages.append(_serialize_message(message))


def _serialize_message(
    message: aio_pika.abc.AbstractIncomingMessage,
) -> universe_snapshot_pb2.Message:
    snapshot_message = universe_snapshot_pb2.Message(
        body=bytes(message.body),
        exchange=message.exchange or "",
        routing_key=message.routing_key or "",
        headers=_to_field_table(dict(message.headers or {})),
    )
    if message.priority is not None:
        snapshot_message.priority = message.priority
    if message.delivery_mode is not None:
        snapshot_message.delivery_mode = int(message.delivery_mode)
    if message.expiration is not None:
        # aio-pika decodes the expiration as seconds; a timedelta is accepted as well.
        expiration = message.expiration
        snapshot_message.expiration = (
            expiration.total_seconds()
            if isinstance(expiration, datetime.timedelta)
            else float(expiration)
        )
    if message.timestamp is not None:
        snapshot_message.timestamp = int(message.timestamp.timestamp())
    # `user_id` is left out: RabbitMQ rejects a message whose user differs from the restoring connection user.
    for field in (
        "content_type",
        "content_encoding",
        "correlation_id",
        "message_id",
        "type",
        "app_id",
        "reply_to",
    ):
        value = getattr(message, field)
        if value is not None:
            setattr(snapshot_message, field, value)
    return snapshot_message


def _to_field_table(values: dict[str, Any]) -> universe_snapshot_pb2.FieldTable:
    table = universe_snapshot_pb2.FieldTable()
    for key, value in values.items():
        field_value = _to_field_value(value)
        if field_value is not None:
            table.fields[key].CopyFrom(field_value)
    return table


def _to_field_value(value: Any) -> universe_snapshot_pb2.FieldValue | None:
    """Convert an AMQP field value, values without a protobuf equivalent are kept as their string form."""
    if value is None:
        return None
    # bool is checked first, it is a subclass of int.
    if isinstance(value, bool):
        return universe_snapshot_pb2.FieldValue(bool_value=value)
    if isinstance(value, int):
        return universe_snapshot_pb2.FieldValue(int_value=value)
    if isinstance(value, float):
        return universe_snapshot_pb2.FieldValue(float_value=value)
    if isinstance(value, (bytes, bytearray)):
        return universe_snapshot_pb2.FieldValue(bytes_value=bytes(value))
    if isinstance(value, dict):
        return universe_snapshot_pb2.FieldValue(table_value=_to_field_table(value))
    if isinstance(value, (list, tuple)):
        array = universe_snapshot_pb2.FieldArray()
        for item in value:
            item_value = _to_field_value(item)
            if item_value is not None:
                array.values.append(item_value)
        return universe_snapshot_pb2.FieldValue(array_value=array)
    return universe_snapshot_pb2.FieldValue(string_value=str(value))


def _from_field_table(table: universe_snapshot_pb2.FieldTable) -> dict[str, Any]:
    return {key: _from_field_value(value) for key, value in table.fields.items()}


def _from_field_value(value: universe_snapshot_pb2.FieldValue) -> Any:
    kind = value.WhichOneof("value")
    if kind == "table_value":
        return _from_field_table(value.table_value)
    if kind == "array_value":
        return [_from_field_value(item) for item in value.array_value.values]
    if kind == "bytes_value":
        # AMQP field tables carry byte arrays as bytearray, plain bytes are rejected by the encoder.
        return bytearray(value.bytes_value)
    if kind is None:
        return None
    return getattr(value, kind)


def _dump_redis(redis_url: str) -> list[universe_snapshot_pb2.RedisKey]:
    keys = []
    with redis.Redis.from_url(redis_url) as client:
        for key in client.scan_iter(count=1000):
            if key.startswith(snapshot.RUN_KEY_PREFIX) is True:
                continue
            value = client.dump(key)
            ttl_ms = client.pttl(key)
            if value is None or ttl_ms == -2:
                # The key expired between the scan and the dump.
                continue
            keys.append(
                universe_snapshot_pb2.RedisKey(
                    key=key, ttl_ms=max(ttl_ms, 0), value=value
                )
            )
    return keys


def _restore_redis(redis_url: str, universe_snapshot: snapshot.Snapshot) -> None:
    with redis.Redis.from_url(redis_url) as client:
        pipeline = client.pipeline(transaction=False)
        for redis_key in universe_snapshot.proto.redis_keys:
            pipeline.restore(
                redis_key.key, redis_key.ttl_ms, redis_key.value, replace=True
            )
        pipeline.execute()


async def _restore_mq(mq_url: str, universe_snapshot: snapshot.Snapshot) -> None:
    connection = await aio_pika.connect(mq_url)
    try:
        channel = await connection.channel(publisher_confirms=True)
        exchanges = {}
        for exchange in universe_snapshot.proto.exchanges:
            exchanges[exchange.name] = await channel.declare_exchange(
                exchange.name,
                type=exchange.type,
                durable=exchange.durable,
                auto_delete=exchange.auto_delete,
                arguments=_from_field_table(exchange.arguments),
            )
        restore_exchange = await channel.declare_exchange(
            RESTORE_EXCHANGE, type=aio_pika.ExchangeType.HEADERS, auto_delete=False
        )
        try:
            for queue in universe_snapshot.proto.queues:
                await _restore_queue(channel, exchanges, restore_exchange, queue)
        finally:
            # A channel closed by a broker error cannot delete the exchange, the original error is kept instead.
            if channel.is_closed is False:
                await restore_exchange.delete()
    finally:
        await connection.close()


async def _restore_queue(
    channel: aio_pika.abc.AbstractChannel,
    exchanges: dict[str, aio_pika.abc.AbstractExchange],
    restore_exchange: aio_pika.abc.AbstractExchange,
    queue: universe_snapshot_pb2.Queue,
) -> None:
    mq_queue = await channel.declare_queue(
        queue.name,
        durable=queue.durable,
        arguments=_from_field_table(queue.arguments),
    )
    for binding in queue.bindings:
        exchange = exchanges.get(binding.exchange)
        if exchange is None:
            raise snapshot.InvalidSnapshotError(
                f"queue {queue.name} is bound to unknown exchange {binding.exchange}"
            )
        await mq_queue.bind(
            exchange,
            routing_key=binding.routing_key,
            arguments=_from_field_table(binding.arguments),
        )
    restore_binding = {"x-match": "all", RESTORE_QUEUE_HEADER: queue.name}
    await mq_queue.bind(restore_exchange, arguments=restore_binding)
    messages = list(queue.messages)
    for start in range(0, len(messages), PUBLISH_BATCH_SIZE):
        await asyncio.gather(
            *(
                restore_exchange.publish(
                    _build_message(message, queue_name=queue.name),
                    routing_key=message.routing_key,
                )
                for message in messages[start : start + PUBLISH_BATCH_SIZE]
            )
        )
    await mq_queue.unbind(restore_exchange, arguments=restore_binding)


def _build_message(
    message: universe_snapshot_pb2.Message, queue_name: str
) -> aio_pika.Message:
    headers = _from_field_table(message.headers)
    headers[RESTORE_QUEUE_HEADER] = queue_name
    optional_fields = {
        field: getattr(message, field)
        for field in (
            "priority",
            "delivery_mode",
            "content_type",
            "content_encoding",
            "correlation_id",
            "message_id",
            "type",
            "app_id",
            "reply_to",
            "expiration",
        )
        if message.HasField(field) is True
    }
    if message.HasField("timestamp") is True:
        optional_fields["timestamp"] = datetime.datetime.fromtimestamp(
            message.timestamp, tz=datetime.timezone.utc
        )
    return aio_pika.Message(body=message.body, headers=headers, **optional_fields)


def main(args: list[str] | None = None) -> None:
    """Restore a snapshot from inside the universe network, before the agents of the universe start."""
    parser = argparse.ArgumentParser(description=main.__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    restore_parser = subparsers.add_parser("restore")
    restore_parser.add_argument(
        "--snapshot",
        type=pathlib.Path,
        default=pathlib.Path(snapshot.SNAPSHOT_MOUNT_PATH) / snapshot.SNAPSHOT_FILENAME,
    )
    restore_parser.add_argument("--mq-url", required=True)
    restore_parser.add_argument("--redis-url", required=True)
    parsed_args = parser.parse_args(args)

    logging.basicConfig(level=logging.INFO)
    universe_snapshot = snapshot.Snapshot.from_bytes(parsed_args.snapshot.read_bytes())
    _wait_services_ready(mq_url=parsed_args.mq_url, redis_url=parsed_args.redis_url)
    # The restore runs once: retrying after a partial publish would duplicate messages.
    restore_snapshot(
        universe_snapshot, mq_url=parsed_args.mq_url, redis_url=parsed_args.redis_url
    )


@tenacity.retry(
    stop=tenacity.stop_after_attempt(RESTORE_ATTEMPTS),
    wait=tenacity.wait_fixed(RESTORE_RETRY_WAIT.total_seconds()),
    reraise=True,
)
def _wait_services_ready(mq_url: str, redis_url: str) -> None:
    """Wait for the MQ and Redis services to accept connections, they report running before they do."""
    with redis.Redis.from_url(redis_url) as client:
        client.ping()
    asyncio.run(_check_mq_connection(mq_url))


async def _check_mq_connection(mq_url: str) -> None:
    async with await aio_pika.connect(mq_url):
        pass


if __name__ == "__main__":
    main()
