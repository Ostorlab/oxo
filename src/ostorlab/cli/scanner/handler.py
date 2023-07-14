"""Module responsible for establishing a connection with nats."""

import asyncio
import datetime
import logging
import ssl
import sys
from typing import Optional, Dict

import nats
from nats.js import api as js_api
from nats.js import client as js_client

from ostorlab.agent.message import serializer

DEFAULT_PENDING_BYTES_LIMIT = 400 * 1024 * 1024

DEFAULT_CONNECT_TIMEOUT = 20

DEFAULT_MAX_INFLIGHT = 1

DEFAULT_ACK_WAIT = 120

DEFAULT_PUBLISH_ACK_WAIT = 30

logger = logging.getLogger(__name__)


class Error(Exception):
    """Base Error."""


class ClientBusHandler:
    def __init__(
        self,
        bus_url: str,
        cluster_id: str,
        name: str,
        tls_context: Optional[ssl.SSLContext] = None,
        loop=None,
    ):
        self._bus_url = bus_url
        self._cluster_id = cluster_id
        self._name = name
        self._nc: nats.NATS = nats.NATS()
        self._js: Optional[js_client.JetStreamContext] = None
        self._loop = loop or asyncio.get_event_loop()
        if tls_context is None and bus_url.startswith("tls://"):
            self._tls_context = ssl.create_default_context()
        else:
            self._tls_context = tls_context

    async def __aenter__(self) -> "ClientBusHandler":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def connect(self, connect_timeout=DEFAULT_CONNECT_TIMEOUT):
        await self._nc.connect(
            self._bus_url,
            name=self._name,
            tls=self._tls_context,
            connect_timeout=connect_timeout,
            error_cb=self._error_cb,
            closed_cb=self._closed_cb,
            reconnected_cb=self._reconnected_cb,
        )
        self._js = self._nc.jetstream()

    async def add_stream(self, name, subjects):
        await self._js.add_stream(name=name, subjects=subjects)

    async def delete_stream(self, name):
        try:
            await self._js.delete_stream(name=name)
        except Exception as e:
            logger.warning("error deleting stream %s: %s", name, e)

    async def close(self):
        await self._nc.close()

    async def publish(
        self,
        subject: str,
        request: Dict,
        ack_wait: int = DEFAULT_PUBLISH_ACK_WAIT,
        stream=None,
    ) -> None:
        """Publish a message to NATS streaming."""
        await self._nc.publish(
            subject, serializer.serialize(subject, request).SerializeToString()
        )

    async def _error_cb(self, e):
        logger.error("Error: %s", e)

    async def _closed_cb(self):
        logger.debug("Connection to Bus is closed.")

    async def _reconnected_cb(self):
        logger.debug("Reconnected to Bus at %s...", self._nc.connected_url.netloc)


class BusHandler(ClientBusHandler):
    def __init__(
        self,
        bus_url: str,
        cluster_id: str,
        name: str,
        tls_context: Optional[ssl.SSLContext] = None,
        loop=None,
    ):
        super().__init__(
            bus_url=bus_url,
            cluster_id=cluster_id,
            name=name,
            tls_context=tls_context,
            loop=loop,
        )
        self._subjects_cb_map = {}
        self._last_message_received_time = datetime.datetime.now()

    async def ensure_running_handler(self):
        """Ensure Bus Handler is always running by checking the last received time of a message."""
        while True:
            try:
                logger.debug(
                    "checking last received message %s",
                    self._last_message_received_time,
                )
                await asyncio.sleep(60)
                if (
                    datetime.datetime.now()
                    > self._last_message_received_time + datetime.timedelta(hours=5)
                ):
                    logger.debug(
                        "too long after receiving the last message, restarting all subscriptions"
                    )
                    await self.close()
                    logger.debug("exiting process")
                    sys.exit(5)
            except Exception as e:
                logger.error("Error in ensure running: %s", e)

    async def subscribe(
        self,
        subject: str,
        cb,
        queue: str = "",
        durable_name: Optional[str] = None,
        start_at: str = "first",
        max_inflight: int = DEFAULT_MAX_INFLIGHT,
        manual_acks: bool = True,
        ack_wait: int = DEFAULT_ACK_WAIT,
    ):
        """Start bus subscription.

        :param subject: Subject for the Bus Streaming subscription.
        :param cb: Callback that receive the subject and deserialized Proto message.
        :param queue: Queue group.
        :param durable_name: Durable connection name.
        :param start_at: One of the following options:
           - 'new_only' (default)
           - 'first'
           - 'sequence'
           - 'last_received'
           - 'time'
        :param max_inflight: Max number of message in flight to client.
        :param manual_acks: Toggles auto ack functionality in the subscription callback so that it is implemented by
         the user instead.
        :param ack_wait: How long to wait for an ack before being redelivered previous messages.
        """
        self._subjects_cb_map[subject] = cb

        if start_at == "new_only":
            deliver_policy = js_api.DeliverPolicy.NEW
        elif start_at == "first":
            deliver_policy = js_api.DeliverPolicy.ALL
        elif start_at == "sequence":
            deliver_policy = js_api.DeliverPolicy.BY_START_SEQUENCE
        elif start_at == "last_received":
            deliver_policy = js_api.DeliverPolicy.LAST
        elif start_at == "time":
            deliver_policy = js_api.DeliverPolicy.BY_START_TIME
        else:
            deliver_policy = js_api.DeliverPolicy.NEW

        sub: js_client.Subscription = await self._js.subscribe(
            subject=subject,
            queue=queue,
            config=js_api.ConsumerConfig(
                durable_name=durable_name,
                ack_wait=ack_wait,
                deliver_policy=deliver_policy,
                max_ack_pending=max_inflight,
            ),
            cb=self._process_message,
            manual_ack=manual_acks,
        )

        # Stan client does not expose pending_bytes_limit to the inbox. Default value is too small and causes large
        # files to be dropped. This is a hackish way to override the value
        inbox_sub = self._nc._subs[sub._id]
        inbox_sub.pending_bytes_limit = DEFAULT_PENDING_BYTES_LIMIT

    async def _process_message(self, message):
        try:
            logger.debug(f"process received message {message}")
            self._last_message_received_time = datetime.datetime.now()
            request = serializer.deserialize(message.subject, message.data)
            cb = self._subjects_cb_map[message.subject]
            await cb(message.subject, request)
            logger.debug(f"acking message for {message.subject}")
            await message.ack()
        except Exception as e:
            logger.exception(e)
