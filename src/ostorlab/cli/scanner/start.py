"""Module Responsible for subscribing to nats for different subjects."""

import asyncio
import logging

from ostorlab.apis import scanner_config
from ostorlab.apis.runners import authenticated_runner
from ostorlab.cli.scanner import handler
from ostorlab.cli.scanner import nats_conf
from nats.js import errors

WAIT_SCHEDULE_SCAN = 60  # seconds
logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")


def _handle_exception(context):
    logger.error("Caught Loop Exception: %s", context)


class ScanHandler:
    """Class responsible for handling the subscription to bushandler"""

    def __init__(self):
        self._bus_handlers = []

    async def close(self):
        for handler in self._bus_handlers:  # pylint: disable=W0621
            await handler.close()

    async def _subscribe(self, config, subject, queue, cb, stream, start_at="first"):
        bus_handler = await self._create_bus_handler(config)
        asyncio.create_task(bus_handler.ensure_running_handler())
        await bus_handler.connect()
        await bus_handler.add_stream(name=stream, subjects=[subject])
        await bus_handler.subscribe(
            subject=subject, queue=queue, cb=cb, start_at=start_at
        )
        self._bus_handlers.append(bus_handler)

    async def subscribe_all(self, config):
        for bus_conf in config.subject_bus_configs:
            if bus_conf.subject == "scan.startAgentScan":
                logger.info("subscribing to scan.startAgentScan")
                await self._subscribe(
                    config=config,
                    subject=bus_conf.subject,
                    queue=bus_conf.queue,
                    cb=self._persist_agent_scan,
                    start_at="last_received",
                    stream=bus_conf.queue,
                )
            elif bus_conf.subject in [
                "scan_engine.scan_saved",
                "scan_engine.scan_done",
                "scan_engine.scan_start_request",
            ]:
                logger.info("subscribing to %s", bus_conf.subject)
                await self._subscribe(
                    config=config,
                    subject="scan_engine.scan_done",
                    queue=bus_conf.queue,
                    cb=self._start_scan_scheduling,
                    start_at="last_received",
                    stream=bus_conf.queue,
                )

    async def _message_handler(self, request, cb, config):
        loop = asyncio.get_event_loop()
        scan = await loop.run_in_executor(None, cb, request)
        logger.info("publishing scan_saved event")

        bus_handler = await self._create_bus_handler(config)
        await bus_handler.connect()
        await bus_handler.publish(
            "scan_engine.scan_saved",
            {"scan_id": scan.id, "reference_scan_id": request.reference_scan_id},
            stream="engine_saved",
        )
        logger.info("done persisting scan")
        await bus_handler.close()

    async def _persist_agent_scan(self, request, config):
        await self._message_handler(request, None, config)

    async def _create_bus_handler(self, config):
        bus_handler = handler.BusHandler(
            bus_url=config.bus_url,
            cluster_id=config.bus_cluster_id,
            name=config.bus_client_name,
        )
        return bus_handler

    async def _start_scan_scheduling(self, request):
        logger.info("scheduling scan from request %s", request.scan_id)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, None)
        logger.info("done scheduling scan")


async def connect_nats(config: nats_conf.ScannerConfig, scanner_id: str):
    """connecting to nats.

    Args:
        config: The key to connect to ostorlab.

        scanner_id: The scanner identifier.
    """
    try:
        logger.info("starting bus runner for scanner %s", scanner_id)
        scan_handler = ScanHandler()
        logger.info("connected, subscribing to plans channels ...")
        await scan_handler.subscribe_all(config)
        logger.info("subscribed")
        return scan_handler
    except errors.ServiceUnavailableError as e:
        logger.exception("run exception %s", e)


async def subscribe_to_nats(api_key: str, scanner_id: str):
    """Fetching the scanner configuration and subscribing to nats.

    Args:
        api_key: The key to connect to ostorlab.

        scanner_id: The scanner identifier.
    """
    logger.info("Fetching scanner configuration.")
    runner = authenticated_runner.AuthenticatedAPIRunner(api_key=api_key)
    data = runner.execute(scanner_config.ScannerConfigAPIRequest(scanner_id=scanner_id))
    config = nats_conf.ScannerConfig.from_json(data)

    logger.info("Connecting to nats.")
    loop = asyncio.get_running_loop()
    loop.set_exception_handler(_handle_exception)
    loop.run_until_complete(connect_nats(config, scanner_id))
    try:
        logger.info("starting forever loop")
        loop.run_forever()
    finally:
        logger.info("closing loop")
        loop.close()
