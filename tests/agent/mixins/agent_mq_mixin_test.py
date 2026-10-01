"""Tests for MQMixin module."""

import asyncio
import concurrent.futures
import logging
from collections import abc
from unittest import mock

import aio_pika
import pytest
import pytest_asyncio
from aiormq import abc as aiormq_abc
from aiormq import exceptions as aiormq_exceptions
from pamqp import commands
from pamqp import header
from pytest_mock import plugin

from ostorlab.agent import agent
from ostorlab.agent import definitions as agent_definitions
from ostorlab.agent.message import message as agent_message
from ostorlab.agent.mixins import agent_mq_mixin
from ostorlab.runtimes import definitions as runtime_definitions
from ostorlab.utils import strings


class Agent(agent_mq_mixin.AgentMQMixin):
    """Helper class to test MQ implementation of send and process messages."""

    def __init__(
        self, name="test1", keys=("a.#",), url="amqp://guest:guest@localhost:5672/"
    ):
        topic = "test_topic"
        super().__init__(name=name, keys=keys, url=url, topic=topic)
        self.stub = None

    def process_message(self, selector, message):
        """Process the MQ messages using stub callback for the Unit tests."""
        if self.stub is not None:
            self.stub(message)

    @classmethod
    def create(
        cls, stub, name="test1", keys=("a.#",), url="amqp://guest:guest@localhost:5672/"
    ):
        instance = cls(name=name, keys=keys, url=url)
        instance.stub = stub
        return instance


@pytest.mark.asyncio
@pytest.mark.docker
async def testClient_whenMessageIsSent_processMessageIsCalled(mocker, mq_service):
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
async def testConnection_whenConnectionException_reconnectIsCalled(mocker):
    stub = mocker.stub(name="test1")
    client = Agent.create(
        stub, name="test1", keys=["d.#"], url="amqp://wrong:wrong@localhost:5672/"
    )

    async def connect_robust_fail(*args, **kwargs):
        raise aiormq_exceptions.AMQPConnectionError("connection refused")

    mocker.patch("aio_pika.connect_robust", side_effect=connect_robust_fail)

    task = asyncio.create_task(client.mq_init())

    try:
        await asyncio.wait_for(task, timeout=10)
    except aiormq_exceptions.AMQPConnectionError:
        pass

    assert task.done() is True


@pytest.mark.skip(reason="Needs debugging why MQ is not resending the message")
@pytest.mark.asyncio
@pytest.mark.docker
async def testClient_whenMessageIsRejectedOnce_messageIsRedelivered(mocker, mq_service):
    word = strings.random_string(length=10).encode()
    stub = mocker.stub(name="test2")
    stub.side_effect = [Exception, None]
    client = Agent.create(stub, name="test2", keys=["b.#"])
    await client.mq_init()
    await client.mq_run(delete_queue_first=True)
    # client.mq_send_message(key='b.1.2', message=word)
    await client.async_mq_send_message(key="b.1.2", message=word)
    await asyncio.sleep(1)
    await client.mq_close()
    stub.assert_has_calls([mock.call(word), mock.call(word)])
    assert stub.call_count == 2


@pytest.mark.skip(reason="Needs debugging why MQ is not resending the message")
@pytest.mark.asyncio
@pytest.mark.docker
async def testClient_whenMessageIsRejectedTwoTimes_messageIsDiscarded(
    mocker, mq_service
):
    word = strings.random_string(length=10).encode()
    stub = mocker.stub(name="test3")
    stub.side_effect = [Exception, Exception, None]
    client = Agent.create(stub, name="test3", keys=["c.#"])
    await client.mq_init()
    await client.mq_run(delete_queue_first=True)
    # client.mq_send_message(key='c.1.2', message=word)
    await client.async_mq_send_message(key="c.1.2", message=word)
    await asyncio.sleep(1)
    await client.mq_close()
    stub.assert_has_calls([mock.call(word), mock.call(word)])
    assert stub.call_count == 2


@pytest.mark.asyncio
@pytest.mark.docker
async def testClient_whenClientDisconnects_messageIsNotLost(mocker, mq_service):
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
    mocker,
):
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

    channel.declare_queue.assert_awaited_once_with(
        "test_queue",
        auto_delete=False,
        durable=True,
        arguments={"x-max-priority": agent_mq_mixin.DEFAULT_MAX_PRIORITY},
    )


class MessageProcessingAgent(agent.Agent):
    """Exercise the Agent lifecycle with deterministic processing outcomes."""

    def __init__(self) -> None:
        super().__init__(
            agent_definition=agent_definitions.AgentDefinition(
                name="queue-agent", in_selectors=["v3.healthcheck.ping"]
            ),
            agent_settings=runtime_definitions.AgentSettings(key="queue-agent"),
        )
        self.processing_error = ValueError("processing failed")
        self.fail_processing = False
        self.processed_messages: list[agent_message.Message] = []
        self.completed_messages: list[agent_message.Message] = []
        self.cleanup_count = 0
        self.limit_callbacks: list[str] = []

    def process(self, message: agent_message.Message) -> None:
        """Record each processing attempt and optionally fail."""
        self.processed_messages.append(message)
        if self.fail_processing is True:
            raise self.processing_error
        self.completed_messages.append(message)

    def process_cleanup(self) -> None:
        """Record cleanup after each processing attempt."""
        self.cleanup_count += 1

    def on_max_cyclic_process_reached(self, message: agent_message.Message) -> None:
        """Record the established cyclic-limit callback."""
        self.limit_callbacks.append("cyclic")

    def on_max_depth_process_reached(self, message: agent_message.Message) -> None:
        """Record the established depth-limit callback."""
        self.limit_callbacks.append("depth")


@pytest_asyncio.fixture
async def message_processing_agent(
    mocker: plugin.MockerFixture,
) -> abc.AsyncIterator[MessageProcessingAgent]:
    """Create an offline Agent on the running loop and release its executor."""
    mocker.patch("werkzeug.serving.make_server")
    client = MessageProcessingAgent()
    try:
        yield client
    finally:
        client._executor.shutdown(wait=True)


@pytest_asyncio.fixture
async def consumed_message_callback(
    mocker: plugin.MockerFixture,
    message_processing_agent: MessageProcessingAgent,
) -> abc.Callable[[aio_pika.abc.AbstractIncomingMessage], abc.Awaitable[None]]:
    """Register the actual MQ consumer without connecting to a broker."""
    queue = mock.Mock(spec=aio_pika.RobustQueue)
    exchange = mock.Mock(spec=aio_pika.RobustExchange)
    channel = mock.Mock(spec=aio_pika.RobustChannel)
    channel.declare_queue.return_value = queue
    channel.declare_exchange.return_value = exchange
    connection = mock.Mock(spec=aio_pika.RobustConnection)
    connection.channel = mock.AsyncMock(return_value=channel)
    mocker.patch("aio_pika.connect_robust", return_value=connection)

    await message_processing_agent.mq_run()

    callback: abc.Callable[
        [aio_pika.abc.AbstractIncomingMessage], abc.Awaitable[None]
    ] = queue.consume.call_args.args[0]
    queue.consume.assert_awaited_once_with(callback, no_ack=False)
    channel.set_qos.assert_awaited_once_with(prefetch_count=1)
    channel.declare_queue.assert_awaited_once_with(
        f"{message_processing_agent.mq_name}_queue",
        auto_delete=False,
        durable=True,
        arguments={"x-max-priority": agent_mq_mixin.DEFAULT_MAX_PRIORITY},
    )
    queue.bind.assert_awaited_once_with(exchange, "v3.healthcheck.ping.#")
    return callback


def _incoming_message(
    channel: aiormq_abc.AbstractChannel,
    message: agent_message.Message,
    redelivered: bool = False,
    control_agents: tuple[str, ...] = (),
    delivery_tag: int = 1,
) -> aio_pika.IncomingMessage:
    """Build an actual aio-pika delivery around a serialized Agent message."""
    control_message = agent_message.Message.from_data(
        "v3.control",
        {
            "control": {"agents": list(control_agents)},
            "message": message.raw,
        },
    )
    delivery = aiormq_abc.DeliveredMessage(
        delivery=commands.Basic.Deliver(
            delivery_tag=delivery_tag,
            routing_key=f"{message.selector}.message-id",
            redelivered=redelivered,
        ),
        header=header.ContentHeader(body_size=len(control_message.raw)),
        body=control_message.raw,
        channel=channel,
    )
    return aio_pika.IncomingMessage(delivery)


@pytest.mark.asyncio
@pytest.mark.parametrize("redelivered", [False, True])
async def testMqRun_whenAgentSucceeds_acknowledgesAfterCleanup(
    message_processing_agent: MessageProcessingAgent,
    consumed_message_callback: abc.Callable[
        [aio_pika.abc.AbstractIncomingMessage], abc.Awaitable[None]
    ],
    ping_message: agent_message.Message,
    redelivered: bool,
) -> None:
    """Successful Agent processing acknowledges both new and redelivered work."""
    channel = mock.Mock(
        spec=aiormq_abc.AbstractChannel,
        is_closed=False,
        basic_ack=mock.AsyncMock(),
        basic_reject=mock.AsyncMock(),
    )
    incoming_message = _incoming_message(channel, ping_message, redelivered)

    await consumed_message_callback(incoming_message)

    channel.basic_ack.assert_awaited_once_with(delivery_tag=1, multiple=False)
    channel.basic_reject.assert_not_awaited()
    assert incoming_message.processed is True
    assert len(message_processing_agent.processed_messages) == 1
    assert (
        message_processing_agent.processed_messages[0].selector == ping_message.selector
    )
    assert message_processing_agent.processed_messages[0].data == ping_message.data
    assert message_processing_agent.cleanup_count == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("redelivered", [False, True])
async def testMqRun_whenAgentFails_acknowledgesAfterLoggingAndCleanup(
    message_processing_agent: MessageProcessingAgent,
    consumed_message_callback: abc.Callable[
        [aio_pika.abc.AbstractIncomingMessage], abc.Awaitable[None]
    ],
    ping_message: agent_message.Message,
    redelivered: bool,
    caplog: pytest.LogCaptureFixture,
    mocker: plugin.MockerFixture,
) -> None:
    """Caught processing failures consume both new and redelivered work."""
    channel = mock.Mock(
        spec=aiormq_abc.AbstractChannel,
        is_closed=False,
        basic_ack=mock.AsyncMock(),
        basic_reject=mock.AsyncMock(),
    )
    incoming_message = _incoming_message(channel, ping_message, redelivered)
    process_context = mocker.spy(aio_pika.IncomingMessage, "process")
    log_handler = logging.NullHandler()
    flush_logs = mocker.spy(log_handler, "flush")
    mocker.patch.object(agent.logger, "handlers", [log_handler])
    message_processing_agent.fail_processing = True

    assert await consumed_message_callback(incoming_message) is None

    channel.basic_ack.assert_awaited_once_with(delivery_tag=1, multiple=False)
    channel.basic_reject.assert_not_awaited()
    process_context.assert_called_once_with(
        incoming_message, requeue=True, reject_on_redelivered=True
    )
    flush_logs.assert_called_once_with()
    assert incoming_message.processed is True
    assert len(message_processing_agent.processed_messages) == 1
    assert message_processing_agent.completed_messages == []
    assert message_processing_agent.cleanup_count == 1
    assert "Error processing message on selector v3.healthcheck.ping" in caplog.text
    assert "Hello, can you hear me?" in caplog.text
    error_record = next(
        record
        for record in caplog.records
        if record.getMessage()
        == "Error processing message on selector v3.healthcheck.ping"
    )
    assert error_record.exc_info is not None
    assert error_record.exc_info[1] is message_processing_agent.processing_error


@pytest.mark.asyncio
async def testMqRun_whenFailurePrecedesHealthyMessage_stopsFailedProcessingAndContinuesConsumer(
    message_processing_agent: MessageProcessingAgent,
    consumed_message_callback: abc.Callable[
        [aio_pika.abc.AbstractIncomingMessage], abc.Awaitable[None]
    ],
    ping_message: agent_message.Message,
) -> None:
    """A consumed failure stops its processing and leaves the consumer usable."""
    channel = mock.Mock(
        spec=aiormq_abc.AbstractChannel,
        is_closed=False,
        basic_ack=mock.AsyncMock(),
        basic_reject=mock.AsyncMock(),
    )
    failed_delivery = _incoming_message(channel, ping_message, delivery_tag=1)
    healthy_message = agent_message.Message.from_data(
        "v3.healthcheck.ping", {"body": "Independent healthy message"}
    )
    healthy_delivery = _incoming_message(channel, healthy_message, delivery_tag=2)
    message_processing_agent.fail_processing = True

    await consumed_message_callback(failed_delivery)

    assert message_processing_agent.completed_messages == []
    assert message_processing_agent.cleanup_count == 1
    channel.basic_ack.assert_awaited_once_with(delivery_tag=1, multiple=False)
    message_processing_agent.fail_processing = False

    await consumed_message_callback(healthy_delivery)

    assert channel.basic_ack.await_args_list == [
        mock.call(delivery_tag=1, multiple=False),
        mock.call(delivery_tag=2, multiple=False),
    ]
    channel.basic_reject.assert_not_awaited()
    assert failed_delivery.processed is True
    assert healthy_delivery.processed is True
    assert len(message_processing_agent.processed_messages) == 2
    assert len(message_processing_agent.completed_messages) == 1
    assert message_processing_agent.completed_messages[0].data == healthy_message.data
    assert message_processing_agent.cleanup_count == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("cyclic_limit", "depth_limit", "accepted_agents", "expected_callbacks"),
    [
        (0, 0, ["trusted-agent"], []),
        (1, 0, [], ["cyclic"]),
        (0, 2, [], ["depth"]),
    ],
    ids=["unaccepted-sender", "cyclic-limit", "depth-limit"],
)
async def testMqRun_whenAgentDeclinesMessage_acknowledgesWithoutRetry(
    message_processing_agent: MessageProcessingAgent,
    consumed_message_callback: abc.Callable[
        [aio_pika.abc.AbstractIncomingMessage], abc.Awaitable[None]
    ],
    ping_message: agent_message.Message,
    cyclic_limit: int,
    depth_limit: int,
    accepted_agents: list[str],
    expected_callbacks: list[str],
) -> None:
    """Intentional validation skips keep their callbacks and acknowledge work."""
    channel = mock.Mock(
        spec=aiormq_abc.AbstractChannel,
        is_closed=False,
        basic_ack=mock.AsyncMock(),
        basic_reject=mock.AsyncMock(),
    )
    incoming_message = _incoming_message(
        channel,
        ping_message,
        control_agents=("sender-agent", message_processing_agent.name),
    )
    message_processing_agent.cyclic_processing_limit = cyclic_limit
    message_processing_agent.depth_processing_limit = depth_limit
    message_processing_agent.accepted_agents = accepted_agents

    await consumed_message_callback(incoming_message)

    channel.basic_ack.assert_awaited_once_with(delivery_tag=1, multiple=False)
    channel.basic_reject.assert_not_awaited()
    assert incoming_message.processed is True
    assert message_processing_agent.processed_messages == []
    assert message_processing_agent.cleanup_count == 0
    assert message_processing_agent.limit_callbacks == expected_callbacks
