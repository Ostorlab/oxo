"""Tests for MQMixin module."""

import asyncio
import random
import string
from unittest import mock
import pytest

from ostorlab.agent.mq import mq_mixin


class Agent(mq_mixin.MQMixin):
    """Helper class to test MQ implementation of send and process messages."""
    def __init__(self, name='test1', keys=('a.#',)):
        super().__init__(name=name, keys=keys)
        self.stub = None

    def _process_message(self, selector, message):
        if self.stub is not None:
            self.stub(message)

    @classmethod
    def create(cls, stub, name='test1', keys=('a.#',)):
        instance = cls(name=name, keys=keys)
        instance.stub = stub
        return instance


def rand_bytes(size=10):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    rand_string = ''.join(random.choice(letters) for i in range(size))
    return rand_string.encode()


@pytest.mark.asyncio
async def testClient_whenMessageIsSent_processMessageIsCalled(mocker, mq_service):
    word = rand_bytes()
    stub = mocker.stub(name='test1')
    client = Agent.create(stub, name='test1', keys=['d.#'])
    await client.mq_run(delete_queue_first=True)
    await client.async_mq_send_message(key='d.1.2', message=word)
    await asyncio.sleep(1)
    await client.mq_close()
    stub.assert_called_with(word)
    assert stub.call_count == 1


@pytest.mark.asyncio
async def testClient_whenMessageIsRejectedOnce_messageIsRedelivered(mocker, mq_service):
    word = rand_bytes()
    stub = mocker.stub(name='test2')
    stub.side_effect = [Exception, None]
    client = Agent.create(stub, name='test2', keys=['b.#'])
    await client.mq_run(delete_queue_first=True)
    # client.mq_send_message(key='b.1.2', message=word)
    await client.async_mq_send_message(key='b.1.2', message=word)
    await asyncio.sleep(1)
    await client.mq_close()
    stub.assert_has_calls([mock.call(word), mock.call(word)])
    assert stub.call_count == 2


@pytest.mark.asyncio
async def testClient_whenMessageIsRejectedTwoTimes_messageIsDiscarded(mocker, mq_service):
    word = rand_bytes()
    stub = mocker.stub(name='test3')
    stub.side_effect = [Exception, Exception, None]
    client = Agent.create(stub, name='test3', keys=['c.#'])
    await client.mq_run(delete_queue_first=True)
    # client.mq_send_message(key='c.1.2', message=word)
    await client.async_mq_send_message(key='c.1.2', message=word)
    await asyncio.sleep(1)
    await client.mq_close()
    stub.assert_has_calls([mock.call(word), mock.call(word)])
    assert stub.call_count == 2


@pytest.mark.asyncio
async def testClient_whenClientDisconnects_messageIsNotLost(mocker, mq_service):
    word = rand_bytes()
    stub = mocker.stub(name='test4')
    # client to send the message
    client1 = Agent.create(stub, name='test4', keys=['f.#'])
    await client1.mq_run(delete_queue_first=True)
    # client to receive the message
    client2 = Agent.create(stub, name='test5', keys=['e.#'])
    await client2.mq_run(delete_queue_first=True)
    # close the client before the message is received
    await client2.mq_close()
    # send the message
    # client1.mq_send_message(key='e.1.2', message=word)
    await client1.async_mq_send_message(key='e.1.2', message=word)
    # restart the client
    await client2.mq_run()
    await asyncio.sleep(5)
    # close the client to avoid an exception to be raised once the loop is closed.
    await client1.mq_close()
    await client2.mq_close()
    # make sure the message is received and was not deleted
    stub.assert_called_with(word)
    assert stub.call_count == 1
