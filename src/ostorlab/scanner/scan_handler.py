"""Module Responsible for handling scanner loop via API."""

from __future__ import annotations

import datetime
import logging
import random
import time
from typing import Any

import docker
import httpx

from ostorlab.apis import scan_update_state
from ostorlab.apis import scanner_config
from ostorlab.apis import scans_discover
from ostorlab.apis.runners import authenticated_runner
from ostorlab.apis.runners import runner as base_runner
from ostorlab.apis.runners import scanner_runner
from ostorlab.scanner import callbacks
from ostorlab.scanner import firewall
from ostorlab.scanner import resource_checker
from ostorlab.scanner import scanner_conf
from ostorlab.utils import scanner_state_reporter

logger = logging.getLogger(__name__)

WAIT_CHECK_MESSAGES = datetime.timedelta(seconds=5)
UNIVERSE_LABEL = "ostorlab.universe"


class ScanHandler:
    """Class responsible for handling the API scan loop."""

    def __init__(
        self,
        state_reporter: scanner_state_reporter.ScannerStateReporter,
        scan_resource_requirements: dict[str, scanner_conf.ScanResourceRequirements]
        | None = None,
        gcp_logging_credential: str | None = None,
        max_concurrent_scans: int = 1,
    ):
        self._state_reporter = state_reporter
        self._scan_resource_requirements = scan_resource_requirements or {}
        self._gcp_logging_credential = gcp_logging_credential
        self._max_concurrent_scans = max_concurrent_scans
        self._docker_client = docker.from_env()
        self._firewall_enabled: bool = firewall.ensure_firewall_chains()
        self._active_scan_ids: set[int] = set()
        if self._firewall_enabled is False:
            logger.warning(
                "Firewall chain setup failed. Network isolation will be disabled."
            )
        else:
            running_universes = self._get_running_universes()
            if running_universes is not None:
                active_ids = {int(u) for u in running_universes if u.isdigit() is True}
                firewall.cleanup_orphaned_chains(active_scan_ids=active_ids)
                self._active_scan_ids.update(active_ids)

    def close(self) -> None:
        """Close resources and clean up managed scan blacklists for finished scans."""
        if self._firewall_enabled is True and len(self._active_scan_ids) > 0:
            running_universes = self._get_running_universes()
            running_ids = (
                {int(u) for u in running_universes if u.isdigit() is True}
                if running_universes is not None
                else set()
            )
            for scan_id in list(self._active_scan_ids):
                if scan_id not in running_ids:
                    clear_success = firewall.clear_scan_blacklist(scan_id=scan_id)
                    if clear_success is True:
                        self._active_scan_ids.discard(scan_id)
                    else:
                        logger.error(
                            "Failed to clear firewall rules during close for scan %s.",
                            scan_id,
                        )
        self._docker_client.close()

    def handle_messages(
        self,
        runner: scanner_runner.ScannerAPIRunner,
        api_key: str | None = None,
    ) -> None:
        """Scan handler method responsible for fetching messages from the API and triggering the scan."""
        logger.info("Starting main API polling loop.")

        while True:
            running_universes = self._get_running_universes()
            if running_universes is None:
                running_universes_count = self._max_concurrent_scans
            else:
                running_universes_count = len(running_universes)
                finished_scans = [
                    finished_scan_id
                    for finished_scan_id in self._active_scan_ids
                    if str(finished_scan_id) not in running_universes
                ]
                if len(finished_scans) > 0:
                    for finished_scan_id in finished_scans:
                        if self._firewall_enabled is True:
                            clear_success = firewall.clear_scan_blacklist(
                                scan_id=finished_scan_id
                            )
                            if clear_success is True:
                                self._active_scan_ids.discard(finished_scan_id)
                            else:
                                logger.error(
                                    "Failed to clear firewall rules for finished scan %s. Will retry.",
                                    finished_scan_id,
                                )
                        else:
                            self._active_scan_ids.discard(finished_scan_id)

            if running_universes_count > self._max_concurrent_scans:
                logger.error(
                    "Host is running %s universe(s) over a limit of %s. Sleeping...",
                    running_universes_count,
                    self._max_concurrent_scans,
                )
                time.sleep(WAIT_CHECK_MESSAGES.seconds)
                continue

            if running_universes_count == self._max_concurrent_scans:
                logger.debug(
                    "Host is running %s universe(s) for a limit of %s. Sleeping...",
                    running_universes_count,
                    self._max_concurrent_scans,
                )
                time.sleep(WAIT_CHECK_MESSAGES.seconds)
                continue

            scans_list = self._fetch_available_scans(runner=runner)
            if scans_list is None or len(scans_list) == 0:
                logger.debug("No scans available in the queue. Sleeping...")
                time.sleep(WAIT_CHECK_MESSAGES.seconds)
                continue

            reserved_scan = self._reserve_single_scan(
                runner=runner, scans_list=scans_list
            )
            if reserved_scan is None:
                logger.debug(
                    "Failed to reserve any scans from the current batch. Sleeping..."
                )
                time.sleep(WAIT_CHECK_MESSAGES.seconds)
                continue

            scan_id = self._trigger_scan_with_rollback(
                runner=runner, reserved_scan=reserved_scan, api_key=api_key
            )
            if scan_id is None:
                logger.warning("Trigger failed and rolled back. Sleeping...")
                time.sleep(WAIT_CHECK_MESSAGES.seconds)

    def _fetch_available_scans(
        self, runner: scanner_runner.ScannerAPIRunner
    ) -> list[dict[str, Any]]:
        """Fetches the list of discoverable scans from the API."""
        logger.debug("Fetching available scans from Discover API...")
        try:
            response = runner.execute(request=scans_discover.ScansDiscoverAPIRequest())
            data = response.get("data") or {}
            scans_list = (data.get("scans") or {}).get("scans") or []
            logger.info("Discovered %s potential scans.", len(scans_list))
            return scans_list
        except (base_runner.ResponseError, httpx.HTTPError):
            logger.exception("Exception while fetching scans")
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

            try:
                candidate_id = int(candidate_id)
            except (ValueError, TypeError):
                logger.warning(
                    "Invalid scan ID format received from API: %s", candidate_id
                )
                continue

            logger.debug("Attempting to reserve candidate scan ID: %s...", candidate_id)

            try:
                reserve_response = runner.execute(
                    request=scan_update_state.ScanUpdateStateAPIRequest(
                        scan_id=candidate_id,
                        progress="locked",
                        full_details=True,
                        scanner_id=self._state_reporter.scanner_id,
                    )
                )
                data = reserve_response.get("data") or {}
                reserve_data = data.get("updateScan") or {}

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
            except (base_runner.ResponseError, httpx.HTTPError) as e:
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

        try:
            scan_id_val = int(raw_id)
        except (ValueError, TypeError):
            logger.warning(
                "Invalid reserved scan ID format received from API: %s. Skipping.",
                raw_id,
            )
            return None

        scan_key = (reserved_scan.get("agentGroup") or {}).get("key")
        if (
            scan_key is not None
            and self._scan_resource_requirements is not None
            and self._scan_resource_requirements != {}
        ) and (
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
            self._rollback_scan_state(runner=runner, scan_id_val=scan_id_val)
            return None

        blacklisted_ips: list[str]
        raw_blacklisted_ips = reserved_scan.get("blacklistedIps")
        if (
            raw_blacklisted_ips is not None
            and isinstance(raw_blacklisted_ips, list) is True
        ):
            blacklisted_ips = raw_blacklisted_ips
        else:
            blacklisted_ips = []
        if len(blacklisted_ips) > 0:
            if self._firewall_enabled is False:
                logger.error(
                    "Firewall chains not initialized. Cannot enforce blacklist for scan %s. Rolling back.",
                    scan_id_val,
                )
                self._rollback_scan_state(runner=runner, scan_id_val=scan_id_val)
                return None

            if (
                firewall.apply_scan_blacklist(scan_id=scan_id_val, ips=blacklisted_ips)
                is False
            ):
                logger.error(
                    "Failed to apply firewall rules for scan %s. Rolling back.",
                    scan_id_val,
                )
                self._rollback_scan_state(runner=runner, scan_id_val=scan_id_val)
                return None

            self._active_scan_ids.add(scan_id_val)

        logger.info("Handing off scan ID %s to callbacks.start_scan...", scan_id_val)

        try:
            started_scan_id = callbacks.start_scan(
                request=reserved_scan,
                state_reporter=self._state_reporter,
                api_key=api_key,
                gcp_logging_credential=self._gcp_logging_credential,
            )
            if started_scan_id is None:
                logger.warning(
                    "Scan %s could not be started locally (runtime unsupported). Rolling back.",
                    scan_id_val,
                )
                self._rollback_scan_state(runner=runner, scan_id_val=scan_id_val)
                return None
            logger.info(
                "Scan %s successfully started. Local ID: %s",
                scan_id_val,
                started_scan_id,
            )
            return started_scan_id
        except Exception:
            logger.exception(
                "Failed to start scan %s locally. Initiating rollback...",
                scan_id_val,
            )
            self._rollback_scan_state(runner=runner, scan_id_val=scan_id_val)
            return None

    def _rollback_scan_state(
        self, runner: scanner_runner.ScannerAPIRunner, scan_id_val: Any
    ) -> bool:
        """Reverts a scan's progress to not_started if local execution fails."""
        clear_success = True
        try:
            scan_id_int = int(scan_id_val)
            if self._firewall_enabled is True:
                clear_success = firewall.clear_scan_blacklist(scan_id=scan_id_int)
                if clear_success is True:
                    self._active_scan_ids.discard(scan_id_int)
                else:
                    self._active_scan_ids.add(scan_id_int)
                    logger.error(
                        "Failed to clear firewall rules during rollback of scan %s. Retrying in loop.",
                        scan_id_val,
                    )
            else:
                self._active_scan_ids.discard(scan_id_int)
        except (ValueError, TypeError):
            logger.warning("Invalid scan ID format in rollback: %s", scan_id_val)

        try:
            runner.execute(
                request=scan_update_state.ScanUpdateStateAPIRequest(
                    scan_id=scan_id_val, progress="not_started"
                )
            )
            logger.info(
                "Successfully rolled back scan %s state to 'not_started'.", scan_id_val
            )
        except Exception:
            logger.exception("FATAL: Failed to rollback scan %s", scan_id_val)
            return False
        return clear_success

    def _get_running_universes(self) -> set[str] | None:
        """Get set of running universe identifiers from Docker services."""
        try:
            universe_services = self._docker_client.services.list(
                filters={"label": UNIVERSE_LABEL},
            )
        except docker.errors.DockerException:
            logger.exception(
                "Docker error listing services, assuming the host is at capacity."
            )
            return None

        universes = set()
        for universe_service in universe_services:
            labels = (universe_service.attrs.get("Spec") or {}).get("Labels") or {}
            universe = labels.get(UNIVERSE_LABEL)
            if universe is not None:
                universes.add(universe)
        return universes


def start_scan_loop(
    api_key: str | None,
    scanner_id: str,
    state_reporter: scanner_state_reporter.ScannerStateReporter,
    gcp_logging_credential: str | None = None,
    max_concurrent_scans: int = 1,
) -> None:
    """Fetching the scanner configuration and starting the API polling loop.

    Args:
        api_key: The key to connect to ostorlab.
        scanner_id: The scanner identifier.
        state_reporter: instance responsible for reporting the scanner state.
        gcp_logging_credential: GCP Logging JSON credentials for agent containers.
        max_concurrent_scans: Number of universes the host may run at once.
    """
    logger.info("Fetching scanner configuration.")
    runner = authenticated_runner.AuthenticatedAPIRunner(api_key=api_key)
    data = runner.execute(
        request=scanner_config.ScannerConfigAPIRequest(scanner_id=scanner_id)
    )
    config = scanner_conf.ScannerConfig.from_json(config=data)

    if config is None or config.api_key is None:
        logger.error("No config found to start the connection.")
        return

    s_runner = scanner_runner.ScannerAPIRunner(api_key=config.api_key)

    logger.info("Starting scan loop via API.")
    scan_handler = ScanHandler(
        state_reporter=state_reporter,
        scan_resource_requirements=config.scan_resource_requirements,
        gcp_logging_credential=gcp_logging_credential,
        max_concurrent_scans=max_concurrent_scans,
    )
    try:
        scan_handler.handle_messages(runner=s_runner, api_key=api_key)
    finally:
        scan_handler.close()
