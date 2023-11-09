"""Tests for MQMixin module."""

import asyncio
from unittest import mock

import pytest

from ostorlab.agent.mixins import agent_mq_mixin
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
        """Process the MQ messages using stub callback for the unittests."""
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
    task = asyncio.create_task(client.mq_init())

    try:
        await asyncio.wait_for(task, timeout=10)
    except asyncio.TimeoutError:
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
