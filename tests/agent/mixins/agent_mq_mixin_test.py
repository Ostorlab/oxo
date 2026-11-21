"""Tests for MQMixin module."""

from __future__ import annotations

import asyncio
import collections.abc
import concurrent.futures
import contextlib
import threading
import typing
from unittest import mock

import aio_pika
import pytest
from aiormq import exceptions as aiormq_exceptions
from pytest_mock import plugin

from ostorlab.agent.mixins import agent_mq_mixin
from ostorlab.runtimes.local.services import mq
from ostorlab.utils import strings


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
        self.stub: typing.Optional[collections.abc.Callable[[bytes], None]] = None

    def process_message(self, selector: str, message: bytes) -> None:
        """Process the MQ messages using stub callback for the Unit tests."""
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


@pytest.mark.skip(reason="Needs debugging why MQ is not resending the message")
@pytest.mark.asyncio
@pytest.mark.docker
async def testClient_whenMessageIsRejectedOnce_messageIsRedelivered(
    mocker: plugin.MockerFixture, mq_service: mq.LocalRabbitMQ
) -> None:
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
    mocker: plugin.MockerFixture, mq_service: mq.LocalRabbitMQ
) -> None:
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

    channel.declare_queue.assert_awaited_once_with(
        "test_queue",
        auto_delete=False,
        durable=True,
        arguments={"x-max-priority": agent_mq_mixin.DEFAULT_MAX_PRIORITY},
    )


class _DeliveredMessage:
    """A message as aio_pika delivers it, its processing context acknowledges or rejects it."""

    def __init__(self, body: bytes) -> None:
        self.body = body
        self.routing_key = "a.1"
        self.settled = False

    @contextlib.asynccontextmanager
    async def process(
        self, requeue: bool = False, reject_on_redelivered: bool = False
    ) -> collections.abc.AsyncIterator[None]:
        try:
            yield
        finally:
            self.settled = True


class _BlockingAgent(agent_mq_mixin.AgentMQMixin):
    """Holds each message in process_message until the test releases it."""

    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        super().__init__(
            name="test",
            keys=["a.#"],
            url="amqp://guest:guest@localhost:5672/",
            topic="test_topic",
            loop=loop,
        )
        self.started: dict[bytes, threading.Event] = collections.defaultdict(
            threading.Event
        )
        self.release: dict[bytes, threading.Event] = collections.defaultdict(
            threading.Event
        )
        self.idle_while_processing: list[bool] = []
        self.failure: Exception | None = None

    def process_message(self, selector: str, message: bytes) -> None:
        self.idle_while_processing.append(self.is_idle())
        self.started[message].set()
        self.release[message].wait(timeout=5)
        if self.failure is not None:
            raise self.failure


async def _wait_started(agent: _BlockingAgent, body: bytes) -> None:
    await asyncio.get_running_loop().run_in_executor(None, agent.started[body].wait, 5)


def testAgentMqMixin_whenNoMessageWasDelivered_isIdle() -> None:
    """A new agent holds no message."""
    agent = agent_mq_mixin.AgentMQMixin(
        name="test",
        keys=["a.#"],
        url="amqp://guest:guest@localhost:5672/",
        topic="test_topic",
    )

    assert agent.is_idle() is True


@pytest.mark.asyncio
async def testAgentMqMixin_whenMessageIsBeingProcessed_isBusyUntilItIsSettled() -> None:
    """The agent is busy from the delivery of a message until its acknowledgement."""
    agent = _BlockingAgent(asyncio.get_running_loop())
    message = _DeliveredMessage(b"m1")

    processing = asyncio.ensure_future(
        agent._mq_process_message(
            typing.cast(aio_pika.abc.AbstractIncomingMessage, message)
        )
    )
    await _wait_started(agent, b"m1")
    busy = agent.is_idle()
    agent.release[b"m1"].set()
    await processing

    assert agent.idle_while_processing == [False]
    assert busy is False
    assert message.settled is True
    assert agent.is_idle() is True


@pytest.mark.asyncio
async def testAgentMqMixin_whenTwoMessagesAreProcessedAndOneEnds_staysBusyUntilTheOtherEnds() -> (
    None
):
    """The agent counts every message it holds, ending one of two keeps it busy."""
    agent = _BlockingAgent(asyncio.get_running_loop())
    first = asyncio.ensure_future(
        agent._mq_process_message(
            typing.cast(aio_pika.abc.AbstractIncomingMessage, _DeliveredMessage(b"m1"))
        )
    )
    second = asyncio.ensure_future(
        agent._mq_process_message(
            typing.cast(aio_pika.abc.AbstractIncomingMessage, _DeliveredMessage(b"m2"))
        )
    )
    await _wait_started(agent, b"m1")
    await _wait_started(agent, b"m2")

    agent.release[b"m1"].set()
    await first
    after_first = agent.is_idle()
    agent.release[b"m2"].set()
    await second

    assert after_first is False
    assert agent.is_idle() is True


@pytest.mark.asyncio
async def testAgentMqMixin_whenProcessingRaises_isIdleAgainAfterTheMessageIsRejected() -> (
    None
):
    """A message whose processing fails no longer counts once it is rejected."""
    agent = _BlockingAgent(asyncio.get_running_loop())
    agent.failure = ValueError("processing failed")
    agent.release[b"m1"].set()
    message = _DeliveredMessage(b"m1")

    with pytest.raises(ValueError):
        await agent._mq_process_message(
            typing.cast(aio_pika.abc.AbstractIncomingMessage, message)
        )

    assert message.settled is True
    assert agent.is_idle() is True


@pytest.mark.asyncio
async def testAgentMqMixin_whenChannelIsClosedDuringProcessing_isIdleAfterReconnecting(
    mocker: plugin.MockerFixture,
) -> None:
    """A message lost with its channel no longer counts, the reconnection does not leave the agent busy."""
    agent = _BlockingAgent(asyncio.get_running_loop())
    agent.failure = aio_pika.exceptions.ChannelInvalidStateError("closed")
    agent.release[b"m1"].set()
    mq_run = mocker.patch.object(agent, "mq_run", new_callable=mocker.AsyncMock)

    await agent._mq_process_message(
        typing.cast(aio_pika.abc.AbstractIncomingMessage, _DeliveredMessage(b"m1"))
    )

    mq_run.assert_awaited_once()
    assert agent.is_idle() is True
