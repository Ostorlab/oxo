"""Module Responsible for subscribing to nats for different subjects."""
import logging
import asyncio
import functools

from nats.js import errors


from ostorlab.apis import scanner_config
from ostorlab.apis.runners import authenticated_runner
from ostorlab.scanner import handler as scanner_handler
from ostorlab.scanner import nats_conf
from ostorlab.scanner import callbacks
from ostorlab.utils import scanner_state_reporter

WAIT_SCHEDULE_SCAN = 60  # seconds


logger = logging.getLogger(__name__)


def _handle_exception(context):
    """The exception handler for the event loop."""
    logger.error("Caught Loop Exception: %s", context)


class ScanHandler:
    """Class responsible for handling the subscription to bus handler."""

    def __init__(self, state_reporter: scanner_state_reporter.ScannerStateReporter):
        self._bus_handlers = []
        self._state_reporter = state_reporter

    async def close(self) -> None:
        for handler in self._bus_handlers:
            await handler.close()

    async def _subscribe(
        self,
        config: nats_conf.ScannerConfig,
        subject,
        queue,
        cb,
        stream,
        start_at="first",
    ) -> None:
        bus_handler = await self._create_bus_handler(config)
        asyncio.create_task(bus_handler.ensure_running_handler())
        await bus_handler.connect()
        await bus_handler.add_stream(name=stream, subjects=[subject])
        await bus_handler.subscribe(
            subject=subject, queue=queue, cb=cb, start_at=start_at
        )
        self._bus_handlers.append(bus_handler)

    async def subscribe_all(self, config: nats_conf.ScannerConfig) -> None:
        for bus_conf in config.subject_bus_configs:
            await self._subscribe(
                config=config,
                subject=bus_conf.subject,
                queue=bus_conf.queue,
                cb=functools.partial(
                    callbacks.start_scan, state_reporter=self._state_reporter
                ),
                start_at="last_received",
                stream=bus_conf.queue,
            )

            logger.info("subscribing to %s", bus_conf.subject)
            return

    async def _create_bus_handler(
        self, config: nats_conf.ScannerConfig
    ) -> scanner_handler.BusHandler:
        bus_handler = scanner_handler.BusHandler(
            bus_url=config.bus_url,
            cluster_id=config.bus_cluster_id,
            name=config.bus_client_name,
        )
        return bus_handler


async def connect_nats(
    config: nats_conf.ScannerConfig,
    scanner_id: str,
    state_reporter: scanner_state_reporter.ScannerStateReporter,
) -> ScanHandler:
    """connecting to nats.

    Args:
        config: The key to connect to ostorlab.
        scanner_id: The scanner identifier.
        state_reporter: The scanner state report.
    """
    try:
        logger.info("starting bus runner for scanner %s", scanner_id)
        scan_handler = ScanHandler(state_reporter)
        logger.info("connected, subscribing to plans channels ...")
        await scan_handler.subscribe_all(config)
        logger.info("subscribed")
        return scan_handler
    except errors.ServiceUnavailableError as e:
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
        state_reporter: The scanner state report.
    """
    logger.info("Fetching scanner configuration.")
    runner = authenticated_runner.AuthenticatedAPIRunner(api_key=api_key)
    data = runner.execute(scanner_config.ScannerConfigAPIRequest(scanner_id=scanner_id))
    config = nats_conf.ScannerConfig.from_json(data)

    if config is None:
        logger.error("No config found to start the connection.")
        return

    logger.info("Connecting to nats.")
    await connect_nats(config, scanner_id, state_reporter)
