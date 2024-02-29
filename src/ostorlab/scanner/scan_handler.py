"""Module Responsible for subscribing to nats for different subjects."""

import logging
import asyncio
import datetime
from typing import List, Optional

import docker
from docker.models import services
from nats.js import errors as jetstream_errors
from nats import errors as nats_errors

from ostorlab.apis import scanner_config
from ostorlab.apis.runners import authenticated_runner
from ostorlab.scanner import handler as scanner_handler
from ostorlab.scanner import scanner_conf
from ostorlab.scanner import callbacks
from ostorlab.utils import scanner_state_reporter

logger = logging.getLogger(__name__)


WAIT_CHECK_MESSAGES = datetime.timedelta(seconds=5)

logger = logging.getLogger(__name__)


class ScanHandler:
    """Class responsible for handling the subscription to bus handler."""

    def __init__(self, state_reporter: scanner_state_reporter.ScannerStateReporter):
        self._bus_handlers = []
        self._state_reporter = state_reporter
        self._docker_client = docker.from_env()

    async def close(self) -> None:
        for handler in self._bus_handlers:
            await handler.close()

    async def _subscribe(
        self,
        config: scanner_conf.ScannerConfig,
        subject,
        queue,
        stream,
        start_at="first",
    ) -> scanner_handler.BusHandler:
        bus_handler = await self._create_bus_handler(config)
        asyncio.create_task(bus_handler.ensure_running_handler())
        await bus_handler.connect()
        await bus_handler.add_stream(name=stream, subjects=[subject])
        await bus_handler.subscribe(
            subject=subject,
            start_at=start_at,
            durable_name=queue,
        )
        self._bus_handlers.append(bus_handler)
        return bus_handler

    async def subscribe_all(self, config: scanner_conf.ScannerConfig) -> None:
        bus_handlers = []
        for bus_conf in config.subject_bus_configs:
            bus_handler = await self._subscribe(
                config=config,
                subject=bus_conf.subject,
                queue=bus_conf.queue,
                start_at="first",
                stream=bus_conf.queue,
            )
            logger.info("subscribing to %s", bus_conf.subject)
            bus_handlers.append(bus_handler)

        for bus_handler in bus_handlers:
            await self.handle_messages(bus_handler, config)

    async def handle_messages(
        self,
        bus_handler: scanner_handler.BusHandler,
        config: scanner_conf.ScannerConfig,
    ) -> None:
        """Scan handler method responsible for fetching messages from the streaming server,
        parse the messages and trigger the scan.
        The message is acknowledged after the scan is created, and the scan handler can't fetch new messages,
        until the current scan is no longer running.

        Args:
            bus_handler: instance for performing BUS operations.
            config: The scanner configuration; holds credentials for the registry & streaming server.
        """
        scan_id = None
        while True:
            if _is_scan_running(self._docker_client, scan_id=scan_id) is True:
                await asyncio.sleep(WAIT_CHECK_MESSAGES.seconds)
            else:
                try:
                    scan_id = await self._handle_message(bus_handler, config)
                except nats_errors.TimeoutError:
                    # No available message to fetch.
                    await asyncio.sleep(WAIT_CHECK_MESSAGES.seconds)

    async def _handle_message(
        self,
        bus_handler: scanner_handler.BusHandler,
        config: scanner_conf.ScannerConfig,
    ) -> str:
        """Fetch, parse a single message and trigger the corresponding scan."""
        async for msg, request in bus_handler.process_message():
            if request is not None and msg is not None:
                try:
                    scan_id = callbacks.start_scan(
                        subject=msg.subject,
                        request=request,
                        state_reporter=self._state_reporter,
                        registry_conf=config.registry_conf,
                    )
                    await msg.ack()
                    return scan_id
                except Exception as e:
                    logger.exception("Exception: %s", e)
                    await msg.nak()

    async def _create_bus_handler(
        self, config: scanner_conf.ScannerConfig
    ) -> scanner_handler.BusHandler:
        bus_handler = scanner_handler.BusHandler(
            bus_url=config.bus_url,
            cluster_id=config.bus_cluster_id,
            name=config.bus_client_name,
        )
        return bus_handler


def _is_scan_running(
    client: docker.DockerClient, scan_id: Optional[str] = None
) -> bool:
    """Returns True, if docker services with `ostorlab.universe` label exist,
    False otherwise.
    """
    if scan_id is None:
        return False
    scan_services: List[services.Service] = client.services.list(
        filters={"label": f"ostorlab.universe={str(scan_id)}"}
    )
    return len(scan_services) > 0


async def connect_nats(
    config: scanner_conf.ScannerConfig,
    scanner_id: str,
    state_reporter: scanner_state_reporter.ScannerStateReporter,
) -> ScanHandler:
    """connecting to nats.

    Args:
        config: The scanner configuration; holds credentials for the registry & streaming server.
        scanner_id: The scanner identifier.
        state_reporter: instance responsible for reporting the scanner state.
    """
    try:
        logger.info("starting bus runner for scanner %s", scanner_id)
        scan_handler = ScanHandler(state_reporter)
        logger.info("connected, subscribing to plans channels ...")
        await scan_handler.subscribe_all(config)
        logger.info("subscribed")
        return scan_handler
    except jetstream_errors.ServiceUnavailableError as e:
        logger.exception("Failed to establish connection to NATs: %s", e)


async def subscribe_nats(
    api_key: str,
    scanner_id: str,
    state_reporter: scanner_state_reporter.ScannerStateReporter,
) -> None:
    """Fetching the scanner configuration and subscribing to nats.

    Args:
        api_key: The key to connect to ostorlab.
        scanner_id: The scanner identifier.
        state_reporter: instance responsible for reporting the scanner state.
    """
    logger.info("Fetching scanner configuration.")
    runner = authenticated_runner.AuthenticatedAPIRunner(api_key=api_key)
    data = runner.execute(scanner_config.ScannerConfigAPIRequest(scanner_id=scanner_id))
    config = scanner_conf.ScannerConfig.from_json(data)

    if config is None:
        logger.error("No config found to start the connection.")
        return

    logger.info("Connecting to nats.")
    await connect_nats(config, scanner_id, state_reporter)
