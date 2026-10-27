"""MQ Mixin.

Definition of the main methods to publish and consume MQ messages by the agents.
"""

import asyncio
import concurrent.futures
import hashlib
import logging
from collections.abc import Sequence

import aio_pika
import tenacity
from aiormq import exceptions as aiormq_exceptions
from pamqp import commands

from ostorlab import exceptions

logger = logging.getLogger(__name__)
NUMBER_RETRIES = 6
WAIT_FIXED_TIME = 5
DEFAULT_MAX_PRIORITY = 255
PROCESSING_MAX_ATTEMPTS = 3
PROCESSING_BACKOFF_SECONDS = 1
PROCESSING_MAX_BACKOFF_SECONDS = 30
PROCESSING_ATTEMPTS_HEADER = "x-oxo-processing-attempts"
ORIGINAL_ROUTING_KEY_HEADER = "x-oxo-original-routing-key"
ERROR_TYPE_HEADER = "x-oxo-error-type"


class PublishNotConfirmedError(exceptions.OstorlabError):
    """The broker did not confirm that it accepted a publication."""


class AgentMQMixin:
    """MQ Mixin class used to initialize the channel, send messages and process them."""

    def __init__(
        self,
        name: str,
        keys: Sequence[str],
        url: str,
        topic: str,
        loop: asyncio.AbstractEventLoop | None = None,
    ) -> None:
        """Initialize the MQ parameters, the channel pools and the executors to process the messages.
        Args:
            name: Name of the queue.
            keys: Selectors that the queue listens to.
            url: string for the MQ url might contain ssl parameters e.g.`amqps://user:pass@host//`
            topic: string with exchange name
        """
        self._name = name
        self._keys = keys
        self._queue_name = f"{self._name}_queue"
        self._failed_queue_name = f"{self._queue_name}.failed"
        self._url = url
        self._topic = topic
        if loop is not None:
            self._loop = loop
        else:
            try:
                self._loop = asyncio.get_event_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
        self._queue: aio_pika.abc.AbstractRobustQueue | None = None
        self._connection_pool: aio_pika.pool.Pool[
            aio_pika.abc.AbstractRobustConnection
        ] = aio_pika.pool.Pool(self._get_connection, max_size=32, loop=self._loop)
        self._channel_pool: aio_pika.pool.Pool[aio_pika.abc.AbstractRobustChannel] = (
            aio_pika.pool.Pool(self._get_channel, max_size=64, loop=self._loop)
        )

    @property
    def mq_name(self) -> str:
        """Queue base name used for RabbitMQ queue registration."""
        return self._name

    async def _get_connection(self) -> aio_pika.abc.AbstractRobustConnection:
        return await aio_pika.connect_robust(
            url=self._url, loop=self._loop, fail_fast=False
        )

    async def _get_channel(self) -> aio_pika.abc.AbstractRobustChannel:
        async with self._connection_pool.acquire() as connection:
            channel = await connection.channel(
                publisher_confirms=True, on_return_raises=True
            )
            return channel

    async def _get_exchange(
        self, channel: aio_pika.abc.AbstractChannel
    ) -> aio_pika.abc.AbstractExchange:
        return await channel.declare_exchange(
            self._topic,
            type=aio_pika.ExchangeType.TOPIC,
            arguments={"x-max-length": 10000, "x-overflow": "reject-publish"},
        )

    async def mq_init(self, delete_queue_first: bool = False) -> None:
        """Declares the queue to start preparing for receiving messages.
        Args:
            delete_queue_first: Used for testing purposes. To delete pending queues first.
        """
        logger.info("Connecting to %s", self._url)
        connection = await self._get_connection()
        async with connection:
            channel = await connection.channel()
            await self._declare_mq_queue(channel, delete_queue_first)

    async def mq_run(self, delete_queue_first: bool = False) -> None:
        """Use a channel to declare the queue, set the listener on the selectors and consume the received messaged.
        Args:
            delete_queue_first: Used for testing purposes. To delete pending queues first.
        """
        connection = await self._get_connection()
        channel = await connection.channel()
        await self._declare_mq_queue(channel, delete_queue_first)

        if self._queue is None:
            raise ValueError("queue not created")

        await self._queue.consume(self._mq_process_message, no_ack=False)

    async def _declare_mq_queue(
        self,
        channel: aio_pika.abc.AbstractRobustChannel,
        delete_queue_first: bool = False,
    ) -> None:
        """Declare the MQ queue on a given channel.
        The queue is durable, redeclaring the queue will return the same queue
        Args:
            channel: the MQ channel to use for the queues
            delete_queue_first: Used for testing purposes. To delete pending queues first.
        """
        await channel.set_qos(prefetch_count=1)
        exchange = await self._get_exchange(channel)
        if delete_queue_first:
            await channel.queue_delete(self._queue_name)

        self._queue = await channel.declare_queue(
            self._queue_name,
            auto_delete=False,
            durable=True,
            arguments={"x-max-priority": DEFAULT_MAX_PRIORITY},
        )

        await channel.declare_queue(
            self._failed_queue_name, durable=True, auto_delete=False
        )

        if self._queue is None:
            raise ValueError("queue not declared.")

        for k in self._keys:
            await self._queue.bind(exchange, k)

    async def _mq_process_message(
        self, message: aio_pika.abc.AbstractIncomingMessage
    ) -> None:
        """Consumes the MQ messages and calls the process message callback."""
        logger.debug("incoming pika message received")
        original_selector = message.headers.get(
            ORIGINAL_ROUTING_KEY_HEADER, message.routing_key
        )
        selector = (
            original_selector
            if isinstance(original_selector, str)
            else message.routing_key
        )
        if selector is None:
            selector = ""
        try:
            try:
                if not isinstance(original_selector, str):
                    raise TypeError("Message routing key must be a string")
                await self._loop.run_in_executor(
                    self._executor, self.process_message, selector, message.body
                )
            except Exception as error:  # noqa: BLE001 - arbitrary agent callback failures
                logger.warning("Message processing failed (%s)", type(error).__name__)
                try:
                    await self._transfer_failed_message(message, selector, error)
                except (
                    aiormq_exceptions.AMQPError,
                    OSError,
                    RuntimeError,
                    PublishNotConfirmedError,
                ) as transfer_error:
                    logger.warning(
                        "Message transfer failed (%s); requeuing original",
                        type(transfer_error).__name__,
                    )
                    await message.reject(requeue=True)
                    return
            await message.ack()
        except aio_pika.exceptions.ChannelInvalidStateError:
            logger.warning("Channel closed; original delivery remains unacknowledged")

    async def _transfer_failed_message(
        self,
        message: aio_pika.abc.AbstractIncomingMessage,
        selector: str,
        error: Exception,
    ) -> None:
        """Confirm a durable replacement before settling the original delivery."""
        previous_attempts = message.headers.get(PROCESSING_ATTEMPTS_HEADER, 0)
        if not isinstance(previous_attempts, int) or previous_attempts < 0:
            previous_attempts = 0
        attempts = previous_attempts + 1
        exhausted = attempts >= PROCESSING_MAX_ATTEMPTS
        if exhausted is False:
            await asyncio.sleep(
                min(
                    PROCESSING_BACKOFF_SECONDS * 2 ** (attempts - 1),
                    PROCESSING_MAX_BACKOFF_SECONDS,
                )
            )
        headers = dict(message.headers)
        headers[PROCESSING_ATTEMPTS_HEADER] = attempts
        headers[ORIGINAL_ROUTING_KEY_HEADER] = selector
        headers[ERROR_TYPE_HEADER] = type(error).__name__[:128]
        message_id = message.message_id
        if message_id is None:
            message_id = hashlib.sha256(
                selector.encode() + b"\0" + message.body
            ).hexdigest()
        replacement = aio_pika.Message(
            body=message.body,
            headers=headers,
            content_type=message.content_type,
            content_encoding=message.content_encoding,
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            priority=message.priority,
            correlation_id=message.correlation_id,
            reply_to=message.reply_to,
            expiration=None if exhausted is True else message.expiration,
            message_id=message_id,
            timestamp=message.timestamp,
            type=message.type,
            user_id=message.user_id,
            app_id=message.app_id,
        )
        destination = self._failed_queue_name if exhausted is True else self._queue_name
        async with self._channel_pool.acquire() as channel:
            confirmation = await channel.default_exchange.publish(
                message=replacement, routing_key=destination, mandatory=True
            )
            if not isinstance(confirmation, commands.Basic.Ack):
                raise PublishNotConfirmedError("Broker did not acknowledge publication")

    def process_message(self, selector: str, message: bytes) -> None:
        """Callback to implement to process the MQ messages received."""
        raise NotImplementedError()

    async def async_mq_send_message(
        self, key: str, message: bytes, message_priority: int | None = None
    ) -> None:
        """Async Send the message to the provided routing key and its priority.
        Args:
            message: Message to send
            key: Selector where to send the message.
            message_priority: the priority of the message. Default is 0
        """
        logger.debug("sending %s to %s", message, key)
        async with self._channel_pool.acquire() as channel:
            exchange = await self._get_exchange(channel)
            pika_message = aio_pika.Message(
                body=message,
                priority=message_priority if message_priority is not None else 0,
                message_id=hashlib.sha256(key.encode() + b"\0" + message).hexdigest(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            )
            confirmation = await exchange.publish(
                routing_key=key, message=pika_message, mandatory=True
            )
            if not isinstance(confirmation, commands.Basic.Ack):
                raise PublishNotConfirmedError("Broker did not acknowledge publication")

    @tenacity.retry(
        retry=tenacity.retry_if_exception_type(
            (
                aio_pika.exceptions.ConnectionClosed,
                ConnectionResetError,
                concurrent.futures.CancelledError,
                aiormq_exceptions.ChannelInvalidStateError,
                aiormq_exceptions.AMQPConnectionError,
            )
        )
        | tenacity.retry_if_exception_message(match="Connection was not opened"),
        stop=tenacity.stop_after_attempt(NUMBER_RETRIES),
        wait=tenacity.wait_fixed(WAIT_FIXED_TIME),
        reraise=True,
    )
    def mq_send_message(
        self, key: str, message: bytes, message_priority: int | None = None
    ) -> None:
        """The method sends the message to the selected key with the defined priority in async mode .
        Args:
            key: Selector that the queue listens to.
            message: Message to send.
            message_priority: the priority to use for the message default is 0.
        """
        logger.debug("sending %s to %s", message, key)

        if not self._loop.is_running():
            self._loop.run_until_complete(
                self.async_mq_send_message(key, message, message_priority)
            )
        else:
            future = asyncio.run_coroutine_threadsafe(
                self.async_mq_send_message(key, message, message_priority), self._loop
            )
            try:
                result = future.result()
            except Exception as exc:
                logger.warning("The coroutine raised an exception: %s", exc)
                raise
            else:
                logger.debug("The coroutine returned: %s", result)
