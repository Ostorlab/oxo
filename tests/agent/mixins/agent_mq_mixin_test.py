"""Tests for MQMixin module."""

from __future__ import annotations

import asyncio
import collections.abc
import concurrent.futures
import typing
import uuid
from unittest import mock

import aio_pika
import aiormq
import docker
import pytest
import pytest_asyncio
from aiormq import exceptions as aiormq_exceptions
from docker.models import containers
from pamqp import commands
from pamqp import header
from pytest_mock import plugin

from ostorlab.agent.mixins import agent_mq_mixin
from ostorlab.runtimes.local.services import mq
from ostorlab.utils import strings


@pytest.fixture(autouse=True)
def disable_publish_retry_delays(mocker: plugin.MockerFixture) -> None:
    """Exercise all publish retry attempts without waiting for real backoff."""
    mocker.patch("time.sleep")


class Agent(agent_mq_mixin.AgentMQMixin):
    """Helper class to test MQ implementation of send and process messages."""

    def __init__(
        self,
        name: str = "test1",
        keys: collections.abc.Sequence[str] = ("a.#",),
        url: str = "amqp://guest:guest@localhost:5672/",
    ) -> None:
        topic = "test_topic"
        super().__init__(name=name, keys=keys, url=url, topic=topic)
        self.selectors: list[str] = []
        self.stub: typing.Optional[collections.abc.Callable[[bytes], None]] = None

    def process_message(self, selector: str, message: bytes) -> None:
        """Process the MQ messages using stub callback for the Unit tests."""
        self.selectors.append(selector)
        if self.stub is not None:
            self.stub(message)

    async def mq_close(self) -> None:
        """Close the pools used by this test client."""
        await self._channel_pool.close()
        await self._connection_pool.close()

    @classmethod
    def create(
        cls,
        stub: collections.abc.Callable[[bytes], None],
        name: str = "test1",
        keys: collections.abc.Sequence[str] = ("a.#",),
        url: str = "amqp://guest:guest@localhost:5672/",
    ) -> Agent:
        instance = cls(name=name, keys=keys, url=url)
        instance.stub = stub
        return instance


@pytest.mark.asyncio
@pytest.mark.docker
async def testClient_whenMessageIsSent_processMessageIsCalled(
    mocker: plugin.MockerFixture, mq_service: mq.LocalRabbitMQ
) -> None:
    word = strings.random_string(length=10).encode()
    stub = mocker.stub(name="test1")
    client = Agent.create(stub, name="test1", keys=["d.#"])
    await client.mq_init()
    await client.mq_run(delete_queue_first=True)
    await client.async_mq_send_message(key="d.1.2", message=word)
    await asyncio.sleep(1)
    stub.assert_called_with(word)
    assert stub.call_count == 1


@pytest.mark.asyncio
async def testConnection_whenConnectionException_reconnectIsCalled(
    mocker: plugin.MockerFixture,
) -> None:
    stub = mocker.stub(name="test1")
    client = Agent.create(
        stub, name="test1", keys=["d.#"], url="amqp://wrong:wrong@localhost:5672/"
    )

    async def connect_robust_fail(
        *args: typing.Any, **kwargs: typing.Any
    ) -> typing.Never:
        raise aiormq_exceptions.AMQPConnectionError("connection refused")

    mocker.patch("aio_pika.connect_robust", side_effect=connect_robust_fail)

    task = asyncio.create_task(client.mq_init())

    try:
        await asyncio.wait_for(task, timeout=10)
    except aiormq_exceptions.AMQPConnectionError:
        pass

    assert task.done() is True


@pytest.mark.asyncio
@pytest.mark.docker
async def testClient_whenClientDisconnects_messageIsNotLost(
    mocker: plugin.MockerFixture, mq_service: mq.LocalRabbitMQ
) -> None:
    word = strings.random_string(length=10).encode()
    stub = mocker.stub(name="test4")
    # client to send the message
    client1 = Agent.create(stub, name="test4", keys=["f.#"])
    await client1.mq_init()
    await client1.mq_run(delete_queue_first=True)
    # client to receive the message
    client2 = Agent.create(stub, name="test5", keys=["e.#"])
    await client2.mq_init()
    await client2.mq_run(delete_queue_first=True)
    # close the client before the message is received
    # send the message
    # client1.mq_send_message(key='e.1.2', message=word)
    await client1.async_mq_send_message(key="e.1.2", message=word)
    # restart the client
    await client2.mq_init()
    await client2.mq_run()
    await asyncio.sleep(5)
    # close the client to avoid an exception to be raised once the loop is closed.
    # make sure the message is received and was not deleted
    stub.assert_called_with(word)
    assert stub.call_count == 1


def testMqSendMessage_onConnectionResetError_shouldRetriesAndReraise(
    mocker: plugin.MockerFixture,
) -> None:
    mock_send_message = mocker.patch.object(agent_mq_mixin.AgentMQMixin, "_get_channel")
    mock_send_message.side_effect = ConnectionResetError
    agent = agent_mq_mixin.AgentMQMixin(
        name="test",
        keys=["a.#"],
        url="amqp://guest:guest@localhost:5672/",
        topic="test_topic",
    )

    with pytest.raises(ConnectionResetError):
        agent.mq_send_message(key="a.1.2", message=b"test message")

    assert mock_send_message.call_count == 6


def testAgentMqMixin_whenNoCurrentLoop_shouldCreateEventLoop(
    mocker: plugin.MockerFixture,
) -> None:
    """Test that AgentMQMixin creates a loop when none is available."""
    mocker.patch("asyncio.get_event_loop", side_effect=RuntimeError)
    new_event_loop = mocker.patch("asyncio.new_event_loop")
    set_event_loop = mocker.patch("asyncio.set_event_loop")

    agent = agent_mq_mixin.AgentMQMixin(
        name="test",
        keys=["a.#"],
        url="amqp://guest:guest@localhost:5672/",
        topic="test_topic",
    )

    assert agent._loop is new_event_loop.return_value
    set_event_loop.assert_called_once_with(new_event_loop.return_value)


def testAgentMqMixin_whenLoopIsProvided_usesProvidedLoop(
    mocker: plugin.MockerFixture,
) -> None:
    """Test that AgentMQMixin uses the explicitly provided event loop."""
    provided_loop = asyncio.new_event_loop()
    get_event_loop = mocker.patch("asyncio.get_event_loop")
    agent = agent_mq_mixin.AgentMQMixin(
        name="test",
        keys=["a.#"],
        url="amqp://guest:guest@localhost:5672/",
        topic="test_topic",
        loop=provided_loop,
    )
    assert agent._loop is provided_loop
    get_event_loop.assert_not_called()
    provided_loop.close()


def testMqSendMessage_onCanceledError_shouldRetryAndReraise(
    mocker: plugin.MockerFixture,
) -> None:
    """Test that the message is retried when a CancelledError is raised."""
    mock_send_message = mocker.patch.object(agent_mq_mixin.AgentMQMixin, "_get_channel")
    mock_send_message.side_effect = concurrent.futures.CancelledError
    agent = agent_mq_mixin.AgentMQMixin(
        name="test",
        keys=["a.#"],
        url="amqp://guest:guest@localhost:5672/",
        topic="test_topic",
    )

    with pytest.raises(concurrent.futures.CancelledError):
        agent.mq_send_message(key="a.1.2", message=b"test message")

    assert mock_send_message.call_count == 6


def testMqSendMessage_onRuntimeError_shouldRetryAndReraise(
    mocker: plugin.MockerFixture,
) -> None:
    """Test that the message is retried when a RuntimeError is raised.

    This covers the aio_pika `Connection.channel()` transient
    `RuntimeError("Connection was not opened")` raised while a
    `RobustConnection` is reconnecting after a broker disconnect.
    """
    mock_send_message = mocker.patch.object(agent_mq_mixin.AgentMQMixin, "_get_channel")
    mock_send_message.side_effect = RuntimeError("Connection was not opened")
    agent = agent_mq_mixin.AgentMQMixin(
        name="test",
        keys=["a.#"],
        url="amqp://guest:guest@localhost:5672/",
        topic="test_topic",
    )

    with pytest.raises(RuntimeError):
        agent.mq_send_message(key="a.1.2", message=b"test message")

    assert mock_send_message.call_count == 6


def testMqSendMessage_onUnrelatedRuntimeError_shouldNotRetry(
    mocker: plugin.MockerFixture,
) -> None:
    """Test that a RuntimeError unrelated to the reconnect window is not retried."""
    mock_send_message = mocker.patch.object(agent_mq_mixin.AgentMQMixin, "_get_channel")
    mock_send_message.side_effect = RuntimeError("Event loop is closed")
    agent = agent_mq_mixin.AgentMQMixin(
        name="test",
        keys=["a.#"],
        url="amqp://guest:guest@localhost:5672/",
        topic="test_topic",
    )

    with pytest.raises(RuntimeError):
        agent.mq_send_message(key="a.1.2", message=b"test message")

    assert mock_send_message.call_count == 1


@pytest.mark.asyncio
async def testAgentMqMixin_declaresQueueWithDefaultPriority(
    mocker: plugin.MockerFixture,
) -> None:
    """Test that AgentMQMixin always declares a priority queue with the default max priority."""
    channel = mocker.AsyncMock()
    exchange = mocker.AsyncMock()
    queue = mocker.AsyncMock()
    channel.declare_queue.return_value = queue

    agent = agent_mq_mixin.AgentMQMixin(
        name="test",
        keys=["a.#"],
        url="amqp://guest:guest@localhost:5672/",
        topic="test_topic",
    )
    mocker.patch.object(agent, "_get_exchange", return_value=exchange)

    await agent._declare_mq_queue(channel)

    channel.declare_queue.assert_any_await(
        "test_queue",
        auto_delete=False,
        durable=True,
        arguments={"x-max-priority": agent_mq_mixin.DEFAULT_MAX_PRIORITY},
    )


@pytest_asyncio.fixture
async def broker_client(
    mocker: plugin.MockerFixture,
) -> collections.abc.AsyncIterator[tuple[Agent, typing.Any, typing.Any]]:
    """Mock only the broker transport; exercise registration and delivery publicly."""
    channel = mocker.AsyncMock()
    channel.default_exchange.publish.return_value = commands.Basic.Ack(delivery_tag=1)
    channel.declare_exchange.return_value.publish.return_value = commands.Basic.Ack(
        delivery_tag=1
    )
    connection = mocker.AsyncMock()
    connection.channel.return_value = channel
    mocker.patch("aio_pika.connect_robust", return_value=connection)
    client = Agent()
    await client.mq_run()
    callback = channel.declare_queue.return_value.consume.call_args.args[0]
    yield client, channel, callback
    await client.mq_close()


def incoming_message(
    channel: typing.Any,
    *,
    headers: dict[str, typing.Any] | None = None,
    redelivered: bool = False,
) -> aio_pika.IncomingMessage:
    """Construct a real delivery with a mocked AMQP transport."""
    channel.is_closed = False
    return aio_pika.IncomingMessage(
        aiormq.abc.DeliveredMessage(
            delivery=commands.Basic.Deliver(
                delivery_tag=1, routing_key="a.asset.uuid", redelivered=redelivered
            ),
            header=header.ContentHeader(
                properties=commands.Basic.Properties(
                    headers=headers,
                    message_id="stable-id",
                    content_type="application/octet-stream",
                    correlation_id="correlation",
                    priority=9,
                    expiration="60000",
                )
            ),
            body=b"payload",
            channel=channel,
        )
    )


@pytest.mark.asyncio
async def testMqRun_whenHandlerFails_transfersBeforeAcknowledging(
    broker_client: tuple[Agent, typing.Any, typing.Any],
    mocker: plugin.MockerFixture,
) -> None:
    client, channel, callback = broker_client
    client.stub = mocker.Mock(side_effect=ValueError("secret-token"))
    sleep = mocker.patch("asyncio.sleep", new_callable=mock.AsyncMock)
    message = incoming_message(channel)
    await callback(message)
    publish = channel.default_exchange.publish
    assert publish.await_count == 1
    transferred = publish.call_args.kwargs["message"]
    assert transferred.body == message.body
    assert transferred.message_id == "stable-id"
    assert transferred.correlation_id == "correlation"
    assert transferred.priority == 9
    assert transferred.content_type == "application/octet-stream"
    assert transferred.delivery_mode == aio_pika.DeliveryMode.PERSISTENT
    assert transferred.headers["x-oxo-processing-attempts"] == 1
    assert transferred.headers["x-oxo-original-routing-key"] == "a.asset.uuid"
    assert "secret-token" not in str(transferred.headers)
    assert publish.call_args.kwargs["routing_key"] == "test1_queue"
    assert publish.call_args.kwargs["mandatory"] is True
    assert message.processed is True
    calls = channel.mock_calls
    assert calls.index(
        mock.call.default_exchange.publish(**publish.call_args.kwargs)
    ) < calls.index(mock.call.basic_ack(delivery_tag=1, multiple=False))
    sleep.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def testMqRun_whenRetriesExhausted_retainsFailedMessage(
    broker_client: tuple[Agent, typing.Any, typing.Any],
    mocker: plugin.MockerFixture,
) -> None:
    client, channel, callback = broker_client
    client.stub = mocker.Mock(side_effect=ValueError("secret-token"))
    message = incoming_message(
        channel,
        headers={
            "x-oxo-processing-attempts": 2,
            "x-oxo-original-routing-key": "a.asset.uuid",
        },
    )
    await callback(message)
    publish = channel.default_exchange.publish
    assert publish.call_args.kwargs["routing_key"] == "test1_queue.failed"
    transferred = publish.call_args.kwargs["message"]
    assert transferred.headers["x-oxo-processing-attempts"] == 3
    assert transferred.headers["x-oxo-error-type"] == "ValueError"
    assert transferred.expiration is None
    assert message.processed is True
    channel.declare_queue.assert_any_await(
        "test1_queue.failed", durable=True, auto_delete=False
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("previous_attempts", [0, 2, 1_000_000])
@pytest.mark.parametrize(
    "confirmation",
    [None, commands.Basic.Nack(delivery_tag=1), commands.Basic.Reject(delivery_tag=1)],
)
async def testMqRun_whenTransferNotConfirmed_requeuesOriginal(
    broker_client: tuple[Agent, typing.Any, typing.Any],
    mocker: plugin.MockerFixture,
    confirmation: typing.Any,
    previous_attempts: int,
) -> None:
    client, channel, callback = broker_client
    client.stub = mocker.Mock(side_effect=ValueError("failure"))
    sleep = mocker.patch("asyncio.sleep", new_callable=mock.AsyncMock)
    channel.default_exchange.publish.return_value = confirmation
    message = incoming_message(
        channel, headers={"x-oxo-processing-attempts": previous_attempts}
    )
    await callback(message)
    channel.basic_ack.assert_not_awaited()
    channel.basic_reject.assert_awaited_once_with(delivery_tag=1, requeue=True)

    sleep.assert_awaited_once_with(1 if previous_attempts == 0 else 4)


@pytest.mark.asyncio
async def testMqRun_whenRedelivered_executesAndAcknowledges(
    broker_client: tuple[Agent, typing.Any, typing.Any],
    mocker: plugin.MockerFixture,
) -> None:
    client, channel, callback = broker_client
    message = incoming_message(
        channel,
        redelivered=True,
        headers={"x-oxo-original-routing-key": "a.original.uuid"},
    )
    await callback(message)
    assert client.selectors == ["a.original.uuid"]
    assert message.processed is True
    channel.default_exchange.publish.assert_not_awaited()


@pytest.mark.asyncio
async def testMqRun_whenTransferCancelled_leavesOriginalUnacknowledged(
    broker_client: tuple[Agent, typing.Any, typing.Any],
    mocker: plugin.MockerFixture,
) -> None:
    client, channel, callback = broker_client
    client.stub = mocker.Mock(side_effect=ValueError("failure"))
    mocker.patch("asyncio.sleep", new_callable=mock.AsyncMock)
    channel.default_exchange.publish.side_effect = asyncio.CancelledError()
    message = incoming_message(channel)
    with pytest.raises(asyncio.CancelledError):
        await callback(message)
    assert message.processed is False
    channel.basic_ack.assert_not_awaited()
    channel.basic_reject.assert_not_awaited()
    channel.declare_queue.return_value.consume.assert_awaited_once()


@pytest.mark.asyncio
async def testMqSendMessage_whenPublishNotConfirmed_raises(
    broker_client: tuple[Agent, typing.Any, typing.Any],
) -> None:
    client, channel, _callback = broker_client
    channel.declare_exchange.return_value.publish.return_value = commands.Basic.Nack(
        delivery_tag=1
    )
    with pytest.raises(agent_mq_mixin.PublishNotConfirmedError):
        await client.async_mq_send_message("unbound.selector", b"payload")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "failure", [ConnectionResetError(), aiormq_exceptions.ChannelInvalidStateError()]
)
async def testMqRun_whenTransferRaises_requeuesWithoutNewConsumer(
    broker_client: tuple[Agent, typing.Any, typing.Any],
    mocker: plugin.MockerFixture,
    failure: Exception,
) -> None:
    client, channel, callback = broker_client
    client.stub = mocker.Mock(side_effect=ValueError("failure"))
    mocker.patch("asyncio.sleep", new_callable=mock.AsyncMock)
    channel.default_exchange.publish.side_effect = failure
    message = incoming_message(channel)
    await callback(message)
    channel.basic_ack.assert_not_awaited()
    channel.basic_reject.assert_awaited_once_with(delivery_tag=1, requeue=True)
    channel.declare_queue.return_value.consume.assert_awaited_once()


@pytest.mark.asyncio
async def testMqRun_whenChannelLostAfterConfirm_preservesOriginalWithoutNewConsumer(
    broker_client: tuple[Agent, typing.Any, typing.Any],
    mocker: plugin.MockerFixture,
) -> None:
    client, channel, callback = broker_client
    client.stub = mocker.Mock(side_effect=ValueError("failure"))
    mocker.patch("asyncio.sleep", new_callable=mock.AsyncMock)
    channel.basic_ack.side_effect = aiormq_exceptions.ChannelInvalidStateError()
    message = incoming_message(channel)
    await callback(message)
    assert message.processed is False
    channel.basic_reject.assert_not_awaited()
    channel.declare_queue.return_value.consume.assert_awaited_once()


@pytest.mark.asyncio
async def testMqSendMessage_whenPublishing_allowsOptionalOutputsAndKeepsIdentity(
    broker_client: tuple[Agent, typing.Any, typing.Any],
) -> None:
    client, channel, _callback = broker_client
    await client.async_mq_send_message("unbound.selector", b"payload")
    publication = channel.declare_exchange.return_value.publish.call_args.kwargs
    assert publication["mandatory"] is False
    await client.async_mq_send_message("unbound.selector", b"payload")
    repeated = channel.declare_exchange.return_value.publish.call_args.kwargs
    assert repeated["message"].message_id == publication["message"].message_id
    assert publication["message"].message_id is not None


@pytest.fixture(scope="module")
def isolated_broker_container() -> collections.abc.Iterator[containers.Container]:
    """Run an isolated classic-queue broker without touching developer services."""
    docker_client = docker.from_env()
    container = docker_client.containers.run(
        "rabbitmq:3.9-management",
        detach=True,
        auto_remove=True,
        ports={"5672/tcp": ("127.0.0.1", 0)},
        environment={"RABBITMQ_SERVER_ADDITIONAL_ERL_ARGS": "+S 2:2"},
        labels={"oxo-test": "crash-safe-messaging"},
    )
    try:
        yield container
    finally:
        container.stop(timeout=5)
        docker_client.close()


@pytest.fixture
def isolated_broker_url(isolated_broker_container: containers.Container) -> str:
    """Return the dedicated broker's loopback AMQP endpoint."""
    isolated_broker_container.reload()
    bindings = isolated_broker_container.ports["5672/tcp"]
    assert bindings is not None
    return f"amqp://guest:guest@127.0.0.1:{bindings[0]['HostPort']}/"


@pytest_asyncio.fixture
async def live_broker(
    isolated_broker_url: str,
    mocker: plugin.MockerFixture,
) -> collections.abc.AsyncIterator[tuple[str, aio_pika.abc.AbstractRobustConnection]]:
    """Wait for the isolated broker and close every client connection on teardown."""
    connect = aio_pika.connect_robust
    connections: list[aio_pika.abc.AbstractRobustConnection] = []

    async def tracked_connect(
        *args: typing.Any, **kwargs: typing.Any
    ) -> aio_pika.abc.AbstractRobustConnection:
        connection: aio_pika.abc.AbstractRobustConnection = await connect(
            *args, **kwargs
        )
        connections.append(connection)
        return connection

    mocker.patch("aio_pika.connect_robust", side_effect=tracked_connect)
    async with asyncio.timeout(40):
        while True:
            try:
                inspector = await tracked_connect(isolated_broker_url)
                break
            except (OSError, aiormq_exceptions.AMQPConnectionError):
                await asyncio.sleep(0.25)
    try:
        yield isolated_broker_url, inspector
    finally:
        for connection in connections:
            await connection.close()


@pytest.mark.asyncio
@pytest.mark.docker
async def testBroker_whenWorkerDisconnects_redeliversAndExecutes(
    live_broker: tuple[str, aio_pika.abc.AbstractRobustConnection],
) -> None:
    url, inspector = live_broker
    client = Agent(name=f"redelivery-{uuid.uuid4()}", url=url)
    done = asyncio.Event()
    loop = asyncio.get_running_loop()

    def processed(body: bytes) -> None:
        loop.call_soon_threadsafe(done.set)

    client.stub = processed
    await client.mq_init()
    channel = await inspector.channel()
    queue = await channel.get_queue(f"{client.mq_name}_queue")
    await channel.default_exchange.publish(
        aio_pika.Message(b"payload"), routing_key=queue.name
    )
    original = await queue.get()
    assert original is not None
    await channel.close()
    await client.mq_run()
    async with asyncio.timeout(5):
        await done.wait()
    assert client.selectors == [queue.name]
    await client.mq_close()


@pytest.mark.asyncio
@pytest.mark.docker
async def testBroker_whenHandlerFails_retryIsLocalAndEventuallyRetained(
    live_broker: tuple[str, aio_pika.abc.AbstractRobustConnection],
    mocker: plugin.MockerFixture,
) -> None:
    url, inspector = live_broker
    client = Agent(name=f"failing-{uuid.uuid4()}", url=url)
    peer = Agent(name=f"peer-{uuid.uuid4()}", url=url)
    client.stub = mocker.Mock(side_effect=ValueError("secret-token"))
    mocker.patch.object(agent_mq_mixin, "PROCESSING_BACKOFF_SECONDS", 0.01)
    await client.mq_run()
    await peer.mq_run()
    await client.async_mq_send_message("a.original.uuid", b"payload")
    channel = await inspector.channel()
    failed = await channel.get_queue(f"{client.mq_name}_queue.failed")
    async with asyncio.timeout(5):
        while True:
            retained = await failed.get(fail=False)
            if retained is not None:
                break
            await asyncio.sleep(0.02)
    assert client.selectors == ["a.original.uuid"] * 3
    assert peer.selectors == ["a.original.uuid"]
    assert retained.body == b"payload"
    assert retained.headers["x-oxo-processing-attempts"] == 3
    assert retained.headers["x-oxo-error-type"] == "ValueError"
    assert retained.headers["x-oxo-original-routing-key"] == "a.original.uuid"
    assert "secret-token" not in str(retained.headers)
    assert retained.message_id is not None
    assert retained.delivery_mode == aio_pika.DeliveryMode.PERSISTENT
    await retained.ack()
    await client.mq_close()
    await peer.mq_close()


@pytest.mark.asyncio
@pytest.mark.docker
async def testBroker_whenFailedQueueMissing_requeuesOriginalAfterMandatoryReturn(
    live_broker: tuple[str, aio_pika.abc.AbstractRobustConnection],
    mocker: plugin.MockerFixture,
) -> None:
    url, inspector = live_broker
    client = Agent(name=f"returned-{uuid.uuid4()}", url=url)
    client.stub = mocker.Mock(side_effect=ValueError("failure"))
    await client.mq_init()
    channel = await inspector.channel()
    queue = await channel.get_queue(f"{client.mq_name}_queue")
    await channel.queue_delete(f"{client.mq_name}_queue.failed")
    await channel.default_exchange.publish(
        aio_pika.Message(b"payload", headers={"x-oxo-processing-attempts": 2}),
        routing_key=queue.name,
    )
    callback_queue = mocker.patch.object(aio_pika.robust_queue.RobustQueue, "consume")
    await client.mq_run()
    await channel.queue_delete(f"{client.mq_name}_queue.failed")
    callback = callback_queue.call_args.args[0]
    original = await queue.get()
    assert original is not None
    sleep = mocker.spy(asyncio, "sleep")
    await callback(original)
    sleep.assert_any_await(4)
    redelivery = await queue.get()
    assert redelivery is not None
    assert redelivery.redelivered is True
    assert redelivery.body == original.body
    assert redelivery.headers["x-oxo-processing-attempts"] == 2
    sleep.reset_mock()
    await callback(redelivery)
    sleep.assert_any_await(4)
    retained = await queue.get()
    assert retained is not None
    assert retained.body == original.body
    await retained.ack()
    await client.mq_close()


@pytest.mark.asyncio
async def testMqRun_whenRoutingHeaderMalformed_retriesWithoutStrandingDelivery(
    broker_client: tuple[Agent, typing.Any, typing.Any],
    mocker: plugin.MockerFixture,
) -> None:
    client, channel, callback = broker_client
    mocker.patch("asyncio.sleep", new_callable=mock.AsyncMock)
    message = incoming_message(channel, headers={"x-oxo-original-routing-key": 123})
    await callback(message)
    assert message.processed is True
    assert client.selectors == []
    replacement = channel.default_exchange.publish.call_args.kwargs["message"]
    assert replacement.headers["x-oxo-original-routing-key"] == "a.asset.uuid"
    assert replacement.headers["x-oxo-processing-attempts"] == 1


@pytest.mark.asyncio
@pytest.mark.docker
async def testBroker_whenOptionalOutputUnbound_acceptsPublication(
    live_broker: tuple[str, aio_pika.abc.AbstractRobustConnection],
) -> None:
    url, _inspector = live_broker
    client = Agent(name=f"unroutable-{uuid.uuid4()}", url=url)
    await client.async_mq_send_message("unbound.selector", b"payload")
    await client.mq_close()


@pytest.mark.asyncio
@pytest.mark.docker
async def testBroker_whenRestarted_preservesUnackedAndFailedMessages(
    live_broker: tuple[str, aio_pika.abc.AbstractRobustConnection],
    isolated_broker_container: containers.Container,
) -> None:
    url, inspector = live_broker
    client = Agent(name=f"restart-{uuid.uuid4()}", url=url)
    await client.mq_init()
    await client.async_mq_send_message("a.restart.uuid", b"unfinished")
    channel = await inspector.channel()
    queue_name = f"{client.mq_name}_queue"
    queue = await channel.get_queue(queue_name)
    original = await queue.get()
    assert original is not None
    await channel.default_exchange.publish(
        aio_pika.Message(
            b"retained-failure",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        ),
        routing_key=f"{queue_name}.failed",
        mandatory=True,
    )
    await client.mq_close()
    await inspector.close()
    await asyncio.to_thread(isolated_broker_container.restart, timeout=5)
    await asyncio.to_thread(isolated_broker_container.reload)
    bindings = isolated_broker_container.ports["5672/tcp"]
    assert bindings is not None
    restarted_url = f"amqp://guest:guest@127.0.0.1:{bindings[0]['HostPort']}/"

    async with asyncio.timeout(45):
        while True:
            try:
                recovered_connection = await aio_pika.connect_robust(restarted_url)
                break
            except (OSError, aiormq_exceptions.AMQPConnectionError):
                await asyncio.sleep(0.25)
    async with recovered_connection:
        recovered_channel = await recovered_connection.channel()
        recovered_queue = await recovered_channel.get_queue(queue_name)
        recovered = await recovered_queue.get()
        assert recovered is not None
        assert recovered.body == original.body
        assert recovered.message_id == original.message_id
        await recovered.ack()
        failed_queue = await recovered_channel.get_queue(f"{queue_name}.failed")
        failed = await failed_queue.get()
        assert failed is not None
        assert failed.body == b"retained-failure"
        await failed.ack()
