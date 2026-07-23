"""Module Responsible for handling scanner loop via API."""

from __future__ import annotations

import logging
import asyncio
import datetime
import random

import docker
from docker.models import services

from typing import Any

from ostorlab.apis import scanner_config
from ostorlab.apis.runners import authenticated_runner
from ostorlab.apis.runners import scanner_runner
from ostorlab.apis import scans_discover

from ostorlab.apis import scan_update_state
from ostorlab.scanner import scanner_conf
from ostorlab.scanner import callbacks
from ostorlab.utils import scanner_state_reporter

logger = logging.getLogger(__name__)

WAIT_CHECK_MESSAGES = datetime.timedelta(seconds=5)


class ScanHandler:
    """Class responsible for handling the API scan loop."""

    def __init__(self, state_reporter: scanner_state_reporter.ScannerStateReporter):
        self._state_reporter = state_reporter
        self._docker_client = docker.from_env()

    async def close(self) -> None:
        pass

    async def handle_messages(
        self,
        runner: scanner_runner.ScannerAPIRunner,
        api_key: str | None = None,
    ) -> None:
        """Scan handler method responsible for fetching messages from the API and triggering the scan."""
        scan_id = None

        logger.info("Starting main API polling loop.")

        while True:
            if scan_id is not None and self._is_scan_running(scan_id=scan_id) is True:
                logger.info(f"Scan {scan_id} is still running. Sleeping...")
                await asyncio.sleep(WAIT_CHECK_MESSAGES.seconds)
                continue

            if scan_id is not None:
                logger.info(f"Scan {scan_id} has finished. Ready for next.")
            scan_id = None

            scans_list = self._fetch_available_scans(runner)
            if scans_list is None or len(scans_list) == 0:
                logger.debug("No scans available in the queue. Sleeping...")
                await asyncio.sleep(WAIT_CHECK_MESSAGES.seconds)
                continue

            reserved_scan = self._reserve_single_scan(runner, scans_list)
            if reserved_scan is None:
                logger.debug(
                    "Failed to reserve any scans from the current batch. Sleeping..."
                )
                await asyncio.sleep(WAIT_CHECK_MESSAGES.seconds)
                continue

            scan_id = self._trigger_scan_with_rollback(runner, reserved_scan, api_key)
            if scan_id is None:
                logger.warning("Trigger failed and rolled back. Sleeping...")
                await asyncio.sleep(WAIT_CHECK_MESSAGES.seconds)

    def _fetch_available_scans(
        self, runner: scanner_runner.ScannerAPIRunner
    ) -> list[dict[str, Any]]:
        """Fetches the list of discoverable scans from the API."""
        logger.debug("Fetching available scans from Discover API...")
        try:
            response = runner.execute(scans_discover.ScansDiscoverAPIRequest())
            scans_list = response.get("data", {}).get("scans", {}).get("scans", [])
            logger.info(f"Discovered {len(scans_list)} potential scans.")
            return scans_list
        except Exception as e:
            logger.exception(f"Exception while fetching scans: {e}")
            return []

    def _reserve_single_scan(
        self,
        runner: scanner_runner.ScannerAPIRunner,
        scans_list: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        """Shuffles the scan list and attempts to reserve them one by one until successful."""
        logger.debug("Shuffling scan list to prevent lock contention.")
        random.shuffle(scans_list)

        for scan_item in scans_list:
            candidate_id = scan_item.get("id")
            if candidate_id is None:
                continue

            candidate_id = int(candidate_id)
            logger.debug(f"Attempting to reserve candidate scan ID: {candidate_id}...")

            try:
                reserve_response = runner.execute(
                    scan_update_state.ScanUpdateStateAPIRequest(
                        scan_id=candidate_id, progress="locked", full_details=True
                    )
                )
                reserve_data = reserve_response.get("data", {}).get("updateScan", {})

                if reserve_data.get("success") is True:
                    logger.info(
                        f"Successfully locked and reserved scan ID: {candidate_id}."
                    )
                    return reserve_data.get("scan")
                else:
                    logger.debug(
                        f"Scan ID {candidate_id} reservation rejected by API (might be locked by another agent)."
                    )
            except Exception as e:
                logger.warning(f"Exception reserving scan {candidate_id}: {e}")

        logger.info("Exhausted scan list. Could not reserve any scans.")
        return None

    def _trigger_scan_with_rollback(
        self,
        runner: scanner_runner.ScannerAPIRunner,
        reserved_scan: dict[str, Any],
        api_key: str | None,
    ) -> str | None:
        """Attempts to start the scan locally, rolling back the API state if it fails."""
        scan_id_val = int(reserved_scan.get("id"))
        logger.info(f"Handing off scan ID {scan_id_val} to callbacks.start_scan...")

        try:
            started_scan_id = callbacks.start_scan(
                request=reserved_scan,
                state_reporter=self._state_reporter,
                api_key=api_key,
            )
            logger.info(
                f"Scan {scan_id_val} successfully started. Local ID: {started_scan_id}"
            )
            return started_scan_id
        except Exception as e:
            logger.exception(
                f"Failed to start scan {scan_id_val} locally: {e}. Initiating rollback..."
            )
            self._rollback_scan_state(runner, scan_id_val)
            return None

    def _rollback_scan_state(
        self, runner: scanner_runner.ScannerAPIRunner, scan_id_val: Any
    ) -> None:
        """Reverts a scan's progress to not_started if local execution fails."""
        try:
            runner.execute(
                scan_update_state.ScanUpdateStateAPIRequest(
                    scan_id=scan_id_val, progress="not_started"
                )
            )
            logger.info(
                f"Successfully rolled back scan {scan_id_val} state to 'not_started'."
            )
        except Exception as rollback_err:
            logger.exception(
                f"FATAL: Failed to rollback scan {scan_id_val}: {rollback_err}"
            )

    def _is_scan_running(self, scan_id: str) -> bool:
        """Returns True if docker services with `ostorlab.universe` label exist."""
        scan_services: list[services.Service] = self._docker_client.services.list(
            filters={"label": f"ostorlab.universe={str(scan_id)}"}
        )
        is_running = len(scan_services) > 0
        return is_running


async def start_scan_loop(
    api_key: str | None,
    scanner_id: str,
    state_reporter: scanner_state_reporter.ScannerStateReporter,
) -> None:
    """Fetching the scanner configuration and starting the API polling loop.

    Args:
        api_key: The key to connect to ostorlab.
        scanner_id: The scanner identifier.
        state_reporter: instance responsible for reporting the scanner state.
    """
    logger.info("Fetching scanner configuration.")
    runner = authenticated_runner.AuthenticatedAPIRunner(api_key=api_key)
    data = runner.execute(scanner_config.ScannerConfigAPIRequest(scanner_id=scanner_id))
    config = scanner_conf.ScannerConfig.from_json(data)
    s_runner = scanner_runner.ScannerAPIRunner(api_key=config.api_key)

    if config is None:
        logger.error("No config found to start the connection.")
        return

    logger.info("Starting scan loop via API.")
    scan_handler = ScanHandler(state_reporter)
    await scan_handler.handle_messages(runner=s_runner, api_key=api_key)
