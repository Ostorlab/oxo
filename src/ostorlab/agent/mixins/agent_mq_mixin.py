"""MQ Mixin.

Defintion of the main methods to publish and consume MQ messages by the agents.
"""

import asyncio
import concurrent.futures
import logging
from typing import List

import aio_pika

logger = logging.getLogger(__name__)


class AgentMQMixin:
    """MQ Mixin class used to initialize the channel, send messages and process them."""

    def __init__(self,
                 name: str,
                 keys: List[str],
                 url: str,
                 topic: str,
                 max_priority: int = None,
                 loop: asyncio.AbstractEventLoop = None):
        """Initialize the MQ parameters, the channel pools and the executors to process the messages.
        Args:
            name: Name of the queue.
            keys: Selectors that the queue listens to.
            url: string for the MQ url might be contain ssl parameters e.g.`amqps://user:pass@host//`
            topic: string with exchange name
            max_priority: Optional To declare a priority queue, it is a positive int [1, 255],
             indicating the max priority the queue supports.
        """
        self._name = name
        self._keys = keys
        self._queue_name = f'{self._name}_queue'
        self._url = url
        self._topic = topic
        self._loop = loop or asyncio.get_event_loop()
        self._max_priority = max_priority
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
        self._queue = None
        self._connection_pool = aio_pika.pool.Pool(self._get_connection, max_size=32, loop=self._loop)
        self._channel_pool = aio_pika.pool.Pool(self._get_channel, max_size=64, loop=self._loop)

    async def _get_connection(self) -> aio_pika.Connection:
        return await aio_pika.connect_robust(url=self._url, loop=self._loop)

    async def _get_channel(self) -> aio_pika.Channel:
        async with self._connection_pool.acquire() as connection:
            return await connection.channel()

    async def _get_exchange(self, channel: aio_pika.Channel) -> aio_pika.Exchange:
        return await channel.declare_exchange(self._topic,
                                              type=aio_pika.ExchangeType.TOPIC,
                                              arguments={'x-max-length': 10000, 'x-overflow': 'reject-publish'})

    async def mq_init(self, delete_queue_first: bool = False):
        """Declares the queue to start preparing for receiving messages.
        Args:
            delete_queue_first: Used for testing purposes. To delete pending queues first.
        """
        logger.info('Connecting to %s', self._url)
        connection = await self._get_connection()
        async with connection:
            channel = await connection.channel()
            await self._declare_mq_queue(channel, delete_queue_first)

    async def mq_run(self, delete_queue_first: bool = False):
        """Use a channel to declare the queue, set the listener on the selectors and consume the received messaged.
        Args:
            delete_queue_first: Used for testing purposes. To delete pending queues first.
        """
        connection = await self._get_connection()
        channel = await connection.channel()
        await self._declare_mq_queue(channel, delete_queue_first)
        await self._queue.consume(self._mq_process_message, no_ack=False)

    async def _declare_mq_queue(self, channel, delete_queue_first: bool = False):
        """Declare the MQ queue on a given channel.
        The queue is durable, re-declaring the queue will return the same queue
        Args:
            channel: the MQ channel to use for the queues
            delete_queue_first: Used for testing purposes. To delete pending queues first.
        """
        await channel.set_qos(prefetch_count=1)
        exchange = await self._get_exchange(channel)
        if delete_queue_first:
            await channel.queue_delete(self._queue_name)

        if self._max_priority is not None:
            self._queue = await channel.declare_queue(self._queue_name, auto_delete=False, durable=True,
                                                      arguments={'x-max-priority': self._max_priority})
        else:
            self._queue = await channel.declare_queue(self._queue_name, auto_delete=False, durable=True)
        for k in self._keys:
            await self._queue.bind(exchange, k)

    async def _mq_process_message(self, message: aio_pika.IncomingMessage):
        """Consumes the MQ messages and calls the process message callback."""
        logger.debug('incoming pika message received')
        async with message.process(requeue=True, reject_on_redelivered=True):
            result = await self._loop.run_in_executor(self._executor,
                                                      self.process_message,
                                                      message.routing_key,
                                                      message.body)
            logging.debug('The process message result: %s', result)

    def process_message(self, selector, message):
        """Callback to implement to process the MQ messages received."""
        raise NotImplementedError()

    async def async_mq_send_message(self, key: str, message: bytes, message_priority: int = None):
        """Async Send the message to the provided routing key and its priority.
        Args:
            message: Message to send
            key: Selector where to send the message.
            message_priority: the priority of the message. Default is 0
        """
        logger.debug('sending %s to %s', message, key)
        async with self._channel_pool.acquire() as channel:
            exchange = await self._get_exchange(channel)
            pika_message = aio_pika.Message(body=message, priority=message_priority)
            await exchange.publish(routing_key=key, message=pika_message)

    def mq_send_message(self, key, message, message_priority=None):
        """the method sends the message to the selected key with the defined priority in async mode .
        Args:
            keys: Selectors that the queue listens to.
            message: Message to send .
            message_priority: the priority to use for the message default is 0.
        """
        logger.debug('sending %s to %s', message, key)
        if not self._loop.is_running():
            self._loop.run_until_complete(self.async_mq_send_message(key, message, message_priority))
        else:
            self._loop.create_task(self.async_mq_send_message(key, message, message_priority))
