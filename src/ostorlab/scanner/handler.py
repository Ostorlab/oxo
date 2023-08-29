"""Module responsible for establishing a connection with NATS."""

import asyncio
import datetime
import logging
import ssl
import sys
import traceback
from typing import Optional

from nats.js import errors as jetstream_errors
from nats import errors as nats_errors
import nats
from nats.js import api as js_api
from nats.js import client as js_client

from ostorlab.scanner.proto.scan._location import startAgentScan_pb2

DEFAULT_PENDING_BYTES_LIMIT = 400 * 1024 * 1024

DEFAULT_CONNECT_TIMEOUT = datetime.timedelta(seconds=20)

DEFAULT_MAX_INFLIGHT = 1

DEFAULT_ACK_WAIT = datetime.timedelta(seconds=180)


logger = logging.getLogger(__name__)


class ClientBusHandler:
    """Handler for establishing a connection with NATS and performing client operations."""

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

    async def connect(self, connect_timeout=DEFAULT_CONNECT_TIMEOUT.seconds):
        """
        Connect to the NATS server.

        Args:
            connect_timeout: Timeout for establishing the connection. Defaults to DEFAULT_CONNECT_TIMEOUT.
        """
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
        """
        Add a stream to the NATS server.

        Args:
            name: Name of the stream.
            subjects: Subjects for the stream.
        """
        await self._js.add_stream(
            name=name,
            subjects=subjects,
        )

    async def delete_stream(self, name):
        """
        Delete a stream from the NATS server.

        Args:
            name: Name of the stream.
        """
        try:
            await self._js.delete_stream(name=name)
        except jetstream_errors.ObjectDeletedError as e:
            logger.warning("error deleting stream %s: %s", name, e)

    async def close(self):
        """Close the connection to the NATS server."""
        await self._nc.close()

    async def _error_cb(self, e):
        logger.error("Error: %s", e)
        logger.error("Traceback: %s", traceback.print_exc())

    async def _closed_cb(self):
        logger.debug("Connection to Bus is closed.")

    async def _reconnected_cb(self):
        logger.debug("Reconnected to Bus at %s...", self._nc.connected_url.netloc)


class BusHandler(ClientBusHandler):
    """Handler for performing bus operations."""

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
        self._pull_subscription = None

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
            except jetstream_errors.ServiceUnavailableError as e:
                logger.error("Error in ensure running: %s", e)

    async def subscribe(
        self,
        subject: str,
        durable_name: Optional[str] = None,
        start_at: str = "first",
        max_inflight: int = DEFAULT_MAX_INFLIGHT,
        ack_wait: int = DEFAULT_ACK_WAIT.seconds,
    ):
        """Start bus subscription.

        subject: Subject for the Bus Streaming subscription.
        durable_name: Durable connection name.
        start_at: One of the following options:
           - 'new_only' (default)
           - 'first'
           - 'sequence'
           - 'last_received'
           - 'time'
        max_inflight: Max number of message in flight to client.
        ack_wait: How long to wait for an ack before being redelivered previous messages.
        """
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

        self._pull_subscription = await self._js.pull_subscribe(
            subject=subject,
            durable=durable_name,
            config=js_api.ConsumerConfig(
                durable_name=durable_name,
                ack_wait=ack_wait,
                deliver_policy=deliver_policy,
                max_ack_pending=max_inflight,
            ),
        )

    async def process_message(
        self,
    ):
        message = None
        request = None

        if self._pull_subscription is not None:
            try:
                logger.debug("Fetching messages.")
                msgs = await self._pull_subscription.fetch()
                for msg in msgs:
                    message = msg
                    logger.debug("Processing message: %s", message)
                    request = await self.parse_message(message)
                    yield message, request
            except nats_errors.TimeoutError:
                logger.debug("No message to fetch, sleeping..")
                await asyncio.sleep(1)
        yield message, request

    async def parse_message(self, message):
        logger.debug("process received message %s", message)
        self._last_message_received_time = datetime.datetime.now()
        request = startAgentScan_pb2.Message()
        request.ParseFromString(message.data)
        return request
