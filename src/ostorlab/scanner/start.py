import logging
import asyncio

from ostorlab.apis import scanner_config
from ostorlab.apis.runners import authenticated_runner
from ostorlab.scanner import handler as scanner_handler
from ostorlab.scanner import nats_conf
from ostorlab.scanner import callbacks

WAIT_SCHEDULE_SCAN = 60  # seconds


logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")


def _handle_exception(loop, context):
    logger.error("Caught Loop Exception: %s", context)


class ScanHandler:
    def __init__(self):
        self._bus_handlers = []

    async def close(self):
        for handler in self._bus_handlers:
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
            await self._subscribe(
                config=config,
                subject=bus_conf.subject,
                queue=bus_conf.queue,
                cb=callbacks.start_scan,
                start_at="last_received",
                stream=bus_conf.queue,
            )

            logger.info("subscribing to %s", bus_conf.subject)
            return

    async def _create_bus_handler(self, config):
        bus_handler = scanner_handler.BusHandler(
            bus_url=config.bus_url,
            cluster_id=config.bus_cluster_id,
            name=config.bus_client_name,
        )
        return bus_handler


async def connect_nats(config: nats_conf.ScannerConfig, scanner_id: str):
    try:
        logger.info("starting bus runner for scanner %s", scanner_id)
        scan_handler = ScanHandler()
        logger.info("connected, subscribing to plans channels ...")
        await scan_handler.subscribe_all(config)
        logger.info("subscribed")
        return scan_handler
    except Exception as e:
        logger.exception("run exception %s", e)


async def subscribe_to_nats(api_key: str, scanner_id: str):
    runner = authenticated_runner.AuthenticatedAPIRunner(api_key=api_key)
    data = runner.execute(scanner_config.ScannerConfigAPIRequest(scanner_id=scanner_id))
    config = nats_conf.ScannerConfig.from_json(data)
    loop = asyncio.get_running_loop()
    loop.set_exception_handler(_handle_exception)
    loop.run_until_complete(connect_nats(config, scanner_id))
    try:
        logger.info("starting forever loop")
        loop.run_forever()
    finally:
        logger.info("closing loop")
        loop.close()
