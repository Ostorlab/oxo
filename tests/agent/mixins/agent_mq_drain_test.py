"""Cooperative retirement preserves active work and broker acknowledgment order."""

import asyncio
import threading

import aio_pika
import pytest
from pytest_mock import plugin

from ostorlab.agent.mixins import agent_mq_mixin


@pytest.mark.asyncio
async def testDrain_busyWorker_waitsForProcessingAndAcknowledgment(
    mocker: plugin.MockerFixture,
) -> None:
    client = agent_mq_mixin.AgentMQMixin("worker", [], "unused", "topic")
    started = asyncio.Event()
    release = threading.Event()
    ack_entered = asyncio.Event()
    ack_release = asyncio.Event()
    loop = asyncio.get_running_loop()

    def process(selector: str, body: bytes) -> None:
        del selector, body
        loop.call_soon_threadsafe(started.set)
        assert release.wait(5)

    async def acknowledge(*args: object) -> None:
        del args
        ack_entered.set()
        await ack_release.wait()

    message = mocker.Mock(spec=aio_pika.abc.AbstractIncomingMessage)
    message.routing_key = "risk"
    message.body = b"risk"
    message.headers = {}
    message.ack = mocker.AsyncMock(side_effect=acknowledge)
    mocker.patch.object(client, "process_message", side_effect=process)
    callback = asyncio.create_task(client._mq_process_message(message))
    try:
        await asyncio.wait_for(started.wait(), 2)
        drain = asyncio.create_task(client.mq_drain())
        await asyncio.sleep(0)
        assert drain.done() is False
        release.set()
        await asyncio.wait_for(ack_entered.wait(), 2)
        assert drain.done() is False
        ack_release.set()
        await asyncio.wait_for(drain, 2)
        await callback
    finally:
        release.set()
        ack_release.set()
        await callback
        client._executor.shutdown()


@pytest.mark.asyncio
async def testDrain_lateRedeliveredMessage_requeuesWithoutProcessing(
    mocker: plugin.MockerFixture,
) -> None:
    client = agent_mq_mixin.AgentMQMixin("worker", [], "unused", "topic")
    await client.mq_drain()
    message = mocker.Mock(spec=aio_pika.abc.AbstractIncomingMessage)
    message.redelivered = True
    message.reject = mocker.AsyncMock()
    process = mocker.patch.object(client, "process_message")
    await client._mq_process_message(message)
    message.reject.assert_awaited_once_with(requeue=True)
    message.ack.assert_not_called()
    process.assert_not_called()
    client._executor.shutdown()


@pytest.mark.asyncio
async def testDrain_registeredConsumer_cancelsOnceAndPreventsRestart(
    mocker: plugin.MockerFixture,
) -> None:
    client = agent_mq_mixin.AgentMQMixin("worker", [], "unused", "topic")
    connection = mocker.AsyncMock()
    channel = mocker.AsyncMock()
    queue = mocker.AsyncMock()
    queue.consume.return_value = "consumer-tag"
    connection.channel.return_value = channel
    mocker.patch.object(client, "_get_connection", return_value=connection)

    async def declare(*args: object) -> None:
        del args
        client._queue = queue

    mocker.patch.object(client, "_declare_mq_queue", side_effect=declare)
    await client.mq_run()
    await client.mq_drain()
    await client.mq_drain()
    await client.mq_run()
    queue.cancel.assert_awaited_once_with("consumer-tag")
    assert queue.consume.await_count == 1
    await client.mq_close()
    connection.close.assert_awaited_once()
    client._executor.shutdown()


@pytest.mark.asyncio
async def testDrain_cancelledCallback_waitsThroughAcknowledgment(
    mocker: plugin.MockerFixture,
) -> None:
    client = agent_mq_mixin.AgentMQMixin("worker", [], "unused", "topic")
    ack_entered = asyncio.Event()
    ack_release = asyncio.Event()
    acknowledged = asyncio.Event()

    async def acknowledge(*args: object) -> None:
        del args
        ack_entered.set()
        await ack_release.wait()
        acknowledged.set()

    message = mocker.Mock(spec=aio_pika.abc.AbstractIncomingMessage)
    message.routing_key = "risk"
    message.body = b"risk"
    message.headers = {}
    message.ack = mocker.AsyncMock(side_effect=acknowledge)
    mocker.patch.object(client, "process_message")
    callback = asyncio.create_task(client._mq_process_message(message))
    await asyncio.wait_for(ack_entered.wait(), 2)
    callback.cancel()
    await asyncio.sleep(0)
    drain = asyncio.create_task(client.mq_drain())
    await asyncio.sleep(0)
    try:
        assert acknowledged.is_set() is False
        assert drain.done() is False
    finally:
        ack_release.set()
        await asyncio.gather(callback, drain, return_exceptions=True)
        client._executor.shutdown()
    assert acknowledged.is_set() is True


@pytest.mark.asyncio
async def testDrain_duringConsumerRegistration_cancelsNewTag(
    mocker: plugin.MockerFixture,
) -> None:
    client = agent_mq_mixin.AgentMQMixin("worker", [], "unused", "topic")
    registration_started = asyncio.Event()
    registration_finish = asyncio.Event()
    connection = mocker.AsyncMock()
    queue = mocker.AsyncMock()
    mocker.patch.object(client, "_get_connection", return_value=connection)

    async def declare(*args: object) -> None:
        del args
        client._queue = queue

    async def consume(*args: object, **kwargs: object) -> str:
        del args, kwargs
        registration_started.set()
        await registration_finish.wait()
        return "new-tag"

    mocker.patch.object(client, "_declare_mq_queue", side_effect=declare)
    queue.consume.side_effect = consume
    registration = asyncio.create_task(client.mq_run())
    await registration_started.wait()
    drain = asyncio.create_task(client.mq_drain())
    await asyncio.sleep(0)
    assert drain.done() is False
    registration_finish.set()
    await asyncio.gather(registration, drain)
    queue.cancel.assert_awaited_once_with("new-tag")
    await client.mq_close()
    client._executor.shutdown()


@pytest.mark.asyncio
@pytest.mark.parametrize("error", [ConnectionError, TimeoutError])
async def testDrain_cancelFailure_keepsAdmissionClosed(
    mocker: plugin.MockerFixture, error: type[Exception]
) -> None:
    client = agent_mq_mixin.AgentMQMixin("worker", [], "unused", "topic")
    queue = mocker.AsyncMock()
    client._queue = queue
    client._consumer_tag = "tag"
    queue.cancel.side_effect = error("broker unavailable")
    await client.mq_drain()
    message = mocker.Mock(spec=aio_pika.abc.AbstractIncomingMessage)
    message.reject = mocker.AsyncMock()
    message.redelivered = True
    await client._mq_process_message(message)
    message.reject.assert_awaited_once_with(requeue=True)
    message.ack.assert_not_called()
    client._executor.shutdown()


@pytest.mark.asyncio
async def testDrain_closedChannel_doesNotRestartConsumer(
    mocker: plugin.MockerFixture,
) -> None:
    client = agent_mq_mixin.AgentMQMixin("worker", [], "unused", "topic")
    await client.mq_drain()
    message = mocker.Mock(spec=aio_pika.abc.AbstractIncomingMessage)
    message.reject = mocker.AsyncMock(
        side_effect=aio_pika.exceptions.ChannelInvalidStateError("closed")
    )
    restart = mocker.patch.object(client, "mq_run")
    await client._mq_process_message(message)
    restart.assert_not_called()
    client._executor.shutdown()
