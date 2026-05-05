"""Scanner module that run scanner command in daemon mode."""

import asyncio
import logging
import os
import sys
import socket
import multiprocessing
from typing import Optional

import click

from ostorlab import configuration_manager as config_manager
from ostorlab.cli import console as cli_console
from ostorlab.cli.rootcli import rootcli
from ostorlab.scanner import scan_handler
from ostorlab.utils import scanner_state_reporter
from ostorlab.utils import ip

console = cli_console.Console()

logger = logging.getLogger(__name__)

WAIT_CAPTURE_INTERVAL = 300
DEFAULT_SCANNER_LOG_FILE = "~/.ostorlab/scanner.log"
SCANNER_FILE_HANDLER_NAME = "ostorlab-scanner-file"


def _configure_file_logging(log_file: Optional[str]) -> None:
    """Persist scanner logs to a file when requested."""
    if log_file is None:
        return

    log_file_path = os.path.abspath(os.path.expanduser(log_file))
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        if getattr(handler, "name", None) == SCANNER_FILE_HANDLER_NAME:
            return

    file_handler = logging.FileHandler(log_file_path)
    file_handler.name = SCANNER_FILE_HANDLER_NAME
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)s [%(process)d] %(name)s: %(message)s"
        )
    )
    root_logger.addHandler(file_handler)
    if root_logger.level > logging.INFO:
        root_logger.setLevel(logging.INFO)
    logger.info("Persisting on-prem scanner logs to %s.", log_file_path)


async def _start_periodic_persist_state(
    state_reporter: scanner_state_reporter.ScannerStateReporter,
):
    while True:
        await state_reporter.report()
        logger.debug("Reporting the scanner state.")
        await asyncio.sleep(WAIT_CAPTURE_INTERVAL)


@rootcli.command()
@click.option("--scanner-id", help="The scanner identifier.", required=True)
@click.option("--daemon/--no-daemon", help="Run in daemon mode.", default=True)
@click.option(
    "--persist-logs/--no-persist-logs",
    help="Persist on-prem scanner logs to a log file.",
    default=False,
)
@click.option(
    "--log-file",
    help="Path to the scanner log file used with --persist-logs.",
    default=DEFAULT_SCANNER_LOG_FILE,
    show_default=True,
)
@click.option(
    "--parallel",
    help="Number of scans to run in parallel.",
    default=1,
    type=click.IntRange(1, None),
)
@click.pass_context
def scanner(
    ctx: click.core.Context,
    daemon: bool,
    scanner_id: str,
    persist_logs: bool,
    log_file: str,
    parallel: str,
) -> None:
    """Oxo scanner enables running custom instances of scanners.
    Scanner communicates with NATs to receive start scan messages.\n
    """
    if sys.platform != "linux" and sys.platform != "darwin":
        console.error("oxo scanner sub-command is only supported on Unix systems.")
        raise click.exceptions.Exit(2)

    api_key = config_manager.ConfigurationManager().api_key or ctx.obj.get("api_key")
    scanner_log_file = log_file if persist_logs is True else None
    _configure_file_logging(scanner_log_file)

    # The import is done for Windows compatibility.
    import daemon as dm

    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id=scanner_id, hostname=socket.gethostname(), ip=ip.get_ip()
    )
    nb_parallel_scans = int(parallel)
    processes = []

    for _ in range(nb_parallel_scans):
        process = multiprocessing.Process(
            target=start_scanner,
            args=(
                api_key,
                scanner_id,
                state_reporter,
                scanner_log_file,
            ),
        )
        process.start()
        processes.append(process)

    if daemon is True:
        with dm.DaemonContext():
            for process in processes:
                process.join()
    else:
        for process in processes:
            process.join()


def start_scanner(
    api_key: Optional[str],
    scanner_id: str,
    state_reporter: scanner_state_reporter.ScannerStateReporter,
    log_file: Optional[str] = None,
) -> None:
    """Run subscription to nats in event loop.

    Args:
        api_key: The api key to login to the platform.
        scanner_id: The id of the scanner.
        state_reporter: instance responsible for reporting the scanner state.
        log_file: Optional path to persist scanner logs.
    """
    _configure_file_logging(log_file)
    if api_key is None:
        logger.error("No api key provided.")
    loop = asyncio.new_event_loop()
    loop.create_task(_start_periodic_persist_state(state_reporter=state_reporter))
    loop.run_until_complete(
        scan_handler.subscribe_nats(
            api_key=api_key,
            scanner_id=scanner_id,
            state_reporter=state_reporter,
        )
    )
    try:
        logger.debug("Closing loop.")
        loop.run_forever()
    finally:
        logger.debug("closing loop.")
        loop.close()
