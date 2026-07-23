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
from ostorlab.scanner import resource_checker
from ostorlab.utils import scanner_state_reporter

logger = logging.getLogger(__name__)

WAIT_CHECK_MESSAGES = datetime.timedelta(seconds=5)


class ScanHandler:
    """Class responsible for handling the API scan loop."""

    def __init__(
        self,
        state_reporter: scanner_state_reporter.ScannerStateReporter,
        scan_resource_requirements: dict[str, scanner_conf.ScanResourceRequirements]
        | None = None,
    ):
        self._state_reporter = state_reporter
        self._scan_resource_requirements = scan_resource_requirements or {}
        self._docker_client = docker.from_env()

    async def close(self) -> None:
        self._docker_client.close()

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
                logger.debug("Scan %s is still running. Sleeping...", scan_id)
                await asyncio.sleep(WAIT_CHECK_MESSAGES.seconds)
                continue

            if scan_id is not None:
                logger.debug("Scan %s has finished. Ready for next.", scan_id)
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
            logger.info("Discovered %s potential scans.", len(scans_list))
            return scans_list
        except Exception as e:
            logger.exception("Exception while fetching scans: %s", e)
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
            logger.debug("Attempting to reserve candidate scan ID: %s...", candidate_id)

            try:
                reserve_response = runner.execute(
                    scan_update_state.ScanUpdateStateAPIRequest(
                        scan_id=candidate_id, progress="locked", full_details=True
                    )
                )
                reserve_data = reserve_response.get("data", {}).get("updateScan", {})

                if reserve_data.get("success") is True:
                    logger.info(
                        "Successfully locked and reserved scan ID: %s.",
                        candidate_id,
                    )
                    return reserve_data.get("scan")
                else:
                    logger.debug(
                        "Scan ID %s reservation rejected by API (might be locked by another agent).",
                        candidate_id,
                    )
            except Exception as e:
                logger.warning("Exception reserving scan %s: %s", candidate_id, e)

        logger.info("Exhausted scan list. Could not reserve any scans.")
        return None

    def _trigger_scan_with_rollback(
        self,
        runner: scanner_runner.ScannerAPIRunner,
        reserved_scan: dict[str, Any],
        api_key: str | None,
    ) -> str | None:
        """Attempts to start the scan locally, rolling back the API state if it fails."""
        raw_id = reserved_scan.get("id")
        if raw_id is None:
            logger.warning("Reserved scan is missing an 'id'. Skipping.")
            return None
        scan_id_val = int(raw_id)

        scan_key = (reserved_scan.get("agentGroup") or {}).get("key")
        if (
            scan_key is not None
            and self._scan_resource_requirements is not None
            and self._scan_resource_requirements != {}
        ):
            if (
                resource_checker.can_run_scan(
                    scan_key=scan_key,
                    requirements=self._scan_resource_requirements,
                )
                is False
            ):
                logger.warning(
                    "Insufficient host resources for scan %s (key: %s). Rolling back.",
                    scan_id_val,
                    scan_key,
                )
                self._rollback_scan_state(runner, scan_id_val)
                return None

        logger.info("Handing off scan ID %s to callbacks.start_scan...", scan_id_val)

        try:
            started_scan_id = callbacks.start_scan(
                request=reserved_scan,
                state_reporter=self._state_reporter,
                api_key=api_key,
            )
            logger.info(
                "Scan %s successfully started. Local ID: %s",
                scan_id_val,
                started_scan_id,
            )
            return started_scan_id
        except Exception as e:
            logger.exception(
                "Failed to start scan %s locally: %s. Initiating rollback...",
                scan_id_val,
                e,
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
                "Successfully rolled back scan %s state to 'not_started'.", scan_id_val
            )
        except Exception as rollback_err:
            logger.exception(
                "FATAL: Failed to rollback scan %s: %s", scan_id_val, rollback_err
            )

    def _is_scan_running(self, scan_id: str | None) -> bool:
        """Returns True if docker services with `ostorlab.universe` label exist."""
        if scan_id is None:
            return False
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

    if config is None:
        logger.error("No config found to start the connection.")
        return

    s_runner = scanner_runner.ScannerAPIRunner(api_key=config.api_key)

    logger.info("Starting scan loop via API.")
    scan_handler = ScanHandler(
        state_reporter,
        scan_resource_requirements=config.scan_resource_requirements,
    )
    try:
        await scan_handler.handle_messages(runner=s_runner, api_key=api_key)
    finally:
        await scan_handler.close()
