"""Scanner module that run scanner command in daemon mode."""

from __future__ import annotations

import json
import logging
import multiprocessing
import os
import socket
import sys
import threading
import time

import click

try:
    from google.api_core import exceptions as google_api_exceptions
    from google.auth import exceptions as google_auth_exceptions
    from google.cloud import logging as gcp_logging
    from google.cloud.logging import handlers as gcp_logging_handlers
    from google.oauth2 import service_account
except ImportError:
    google_api_exceptions = None
    google_auth_exceptions = None
    gcp_logging = None
    gcp_logging_handlers = None
    service_account = None

from ostorlab import configuration_manager as config_manager
from ostorlab.cli import console as cli_console
from ostorlab.cli.rootcli import rootcli
from ostorlab.scanner import scan_handler
from ostorlab.utils import ip, scanner_state_reporter

console = cli_console.Console()

logger = logging.getLogger(__name__)

WAIT_CAPTURE_INTERVAL = 300
DEFAULT_SCANNER_LOG_FILE = "~/.ostorlab/scanner.log"
DEFAULT_SCANNER_LOG_LEVEL = "INFO"
SCANNER_FILE_HANDLER_NAME = "ostorlab-scanner-file"
SCANNER_LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


def _configure_file_logging(
    log_file: str | None, log_level: int = logging.INFO
) -> None:
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
    file_handler.setLevel(log_level)
    file_handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)s [%(process)d] %(name)s: %(message)s"
        )
    )
    root_logger.addHandler(file_handler)
    if root_logger.level > log_level:
        root_logger.setLevel(log_level)
    logger.info("Persisting on-prem scanner logs to %s.", log_file_path)


def _configure_gcp_logging(gcp_logging_credential: str | None, scanner_id: str) -> None:
    """Attach a labeled Cloud Logging handler to the calling process.

    The root CLI already sets up Cloud Logging, but its background transport thread does not survive the fork
    performed to spawn the scan workers, so every worker must set up its own handler.
    """
    if gcp_logging_credential is None:
        return

    if (
        gcp_logging is None
        or gcp_logging_handlers is None
        or service_account is None
        or google_api_exceptions is None
        or google_auth_exceptions is None
    ):
        logger.error(
            "Could not import Google Cloud Logging, install it with `pip install 'ostorlab[google-cloud-logging]'"
        )
        return

    root_logger = logging.getLogger()
    for handler in list(root_logger.handlers):
        if isinstance(handler, gcp_logging_handlers.CloudLoggingHandler):
            root_logger.removeHandler(handler)

    try:
        credentials = service_account.Credentials.from_service_account_info(
            json.loads(gcp_logging_credential)
        )
        client = gcp_logging.Client(credentials=credentials)
        client.setup_logging(
            labels={
                "scanner_id": scanner_id,
                "hostname": socket.gethostname(),
                "pid": str(os.getpid()),
            }
        )
    except (
        ValueError,
        google_auth_exceptions.GoogleAuthError,
        google_api_exceptions.GoogleAPIError,
    ):
        logger.exception(
            "Could not configure Cloud Logging, scanner logs will only be persisted locally."
        )
        return

    logger.info("Cloud Logging configured for scanner %s.", scanner_id)


def _start_periodic_persist_state(
    state_reporter: scanner_state_reporter.ScannerStateReporter,
):
    while True:
        try:
            state_reporter.report()
            logger.debug("Reporting the scanner state.")
        except Exception:
            logger.exception("Failed to report scanner state, will retry.")
        time.sleep(WAIT_CAPTURE_INTERVAL)


@rootcli.command()
@click.option("--scanner-id", help="The scanner identifier.", required=True)
@click.option("--daemon/--no-daemon", help="Run in daemon mode.", default=True)
@click.option(
    "--persist-logs",
    help="Persist on-prem scanner logs to a log file.",
    is_flag=True,
    flag_value=True,
    default=True,
)
@click.option(
    "--log-file",
    help="Path to the scanner log file used with --persist-logs.",
    default=DEFAULT_SCANNER_LOG_FILE,
    show_default=True,
)
@click.option(
    "--log-level",
    help="Scanner log file verbosity used with --persist-logs.",
    type=click.Choice(SCANNER_LOG_LEVELS, case_sensitive=False),
    default=DEFAULT_SCANNER_LOG_LEVEL,
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
    log_level: str,
    parallel: int,
) -> None:
    """Oxo scanner enables running custom instances of scanners.
    Scanner communicates with NATs to receive start scan messages.\n
    """
    if sys.platform != "linux" and sys.platform != "darwin":
        console.error("oxo scanner sub-command is only supported on Unix systems.")
        raise click.exceptions.Exit(2)

    api_key = config_manager.ConfigurationManager().api_key or ctx.obj.get("api_key")
    gcp_logging_credential = ctx.obj.get("gcp_logging_credential")
    scanner_log_file = log_file if persist_logs is True else None
    scanner_log_level = getattr(logging, log_level.upper())
    _configure_file_logging(scanner_log_file, scanner_log_level)

    # The import is done for Windows compatibility.
    import daemon as dm

    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id=scanner_id,
        hostname=socket.gethostname(),
        ip=ip.get_ip(),
        reporting_engine_api_key=api_key,
    )
    nb_parallel_scans = parallel
    processes = []

    for _ in range(nb_parallel_scans):
        process = multiprocessing.Process(
            target=start_scanner,
            args=(
                api_key,
                scanner_id,
                state_reporter,
                scanner_log_file,
                scanner_log_level,
                gcp_logging_credential,
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
    api_key: str | None,
    scanner_id: str,
    state_reporter: scanner_state_reporter.ScannerStateReporter,
    log_file: str | None = None,
    log_level: int = logging.INFO,
    gcp_logging_credential: str | None = None,
) -> None:
    """Run subscription to nats in event loop.

    Args:
        api_key: The api key to login to the platform.
        scanner_id: The id of the scanner.
        state_reporter: instance responsible for reporting the scanner state.
        log_file: Optional path to persist scanner logs.
        log_level: Logging level used for persisted scanner logs.
        gcp_logging_credential: GCP Logging JSON credentials for agent containers.
    """
    _configure_file_logging(log_file, log_level)
    _configure_gcp_logging(gcp_logging_credential, scanner_id)
    if api_key is None:
        logger.error("No api key provided.")

    persist_thread = threading.Thread(
        target=_start_periodic_persist_state,
        args=(state_reporter,),
        daemon=True,
    )
    persist_thread.start()

    scan_handler.start_scan_loop(
        api_key=api_key,
        scanner_id=scanner_id,
        state_reporter=state_reporter,
        gcp_logging_credential=gcp_logging_credential,
    )
