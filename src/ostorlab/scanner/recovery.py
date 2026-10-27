"""Bounded recovery of stalled local workers, retaining their broker and messages."""

from __future__ import annotations

import json
import logging
import time
import typing

import docker
import httpx
from docker.models import services

from ostorlab.apis import scan_update_state
from ostorlab.apis import scans_active
from ostorlab.apis.runners import runner as base_runner
from ostorlab.apis.runners import scanner_runner
from ostorlab.runtimes.local.services import container_exec

logger = logging.getLogger(__name__)

RECONCILE_INTERVAL_SECONDS = 60
STALL_GRACE_SECONDS = 120
RECOVERY_COOLDOWN_SECONDS = 120
MAX_RECOVERY_ATTEMPTS = 2
MAX_ACTIVE_SCAN_PAGES = 1000
ATTEMPTS_LABEL = "ostorlab.recovery.attempts"
LAST_ATTEMPT_LABEL = "ostorlab.recovery.last_attempt"
QUEUE_COMMAND = [
    "rabbitmqctl",
    "list_queues",
    "--formatter=json",
    "--timeout",
    "10",
    "name",
    "messages_ready",
    "messages_unacknowledged",
    "consumers",
]


def active_scan_ids(runner: scanner_runner.ScannerAPIRunner) -> set[str] | None:
    """Return a complete active scan snapshot, or None if it cannot be established."""
    scan_ids: set[str] = set()
    expected_pages: int | None = None
    try:
        for page in range(1, MAX_ACTIVE_SCAN_PAGES + 1):
            response = runner.execute(request=scans_active.ScansActiveAPIRequest(page))
            if response.get("errors") is not None:
                raise ValueError("active scans response contains errors")
            result = response["data"]["scans"]
            num_pages = result["pageInfo"]["numPages"]
            entries = result["scans"]
            if (
                type(num_pages) is not int
                or num_pages < 0
                or num_pages > MAX_ACTIVE_SCAN_PAGES
            ):
                raise ValueError("invalid active scans page count")
            if expected_pages is not None and expected_pages != num_pages:
                raise ValueError("active scans pagination changed during enumeration")
            expected_pages = num_pages
            if not isinstance(entries, list) or (len(entries) == 0 and num_pages > 1):
                raise ValueError("incomplete active scans page")
            for entry in entries:
                scan_id = str(entry["id"])
                if not scan_id.isdecimal() or scan_id in scan_ids:
                    raise ValueError("invalid or duplicate active scan ID")
                scan_ids.add(scan_id)
            if page >= num_pages:
                return scan_ids
    except (
        base_runner.ResponseError,
        httpx.HTTPError,
        KeyError,
        TypeError,
        ValueError,
    ):
        logger.exception("Cannot establish active scans; skipping worker recovery.")
    return None


def _worker_scan_id(service: services.Service) -> str | None:
    spec = service.attrs["Spec"]
    labels = spec.get("Labels", {})
    scan_id = labels.get("ostorlab.universe")
    queue_name = labels.get("ostorlab.queue_name")
    template = spec.get("TaskTemplate", {})
    owner = template.get("ContainerSpec", {}).get("Labels", {}).get("ostorlab.scan_id")
    replicas = spec.get("Mode", {}).get("Replicated", {}).get("Replicas", 0)
    if (
        not isinstance(scan_id, str)
        or not scan_id.isdecimal()
        or owner != scan_id
        or not isinstance(queue_name, str)
        or queue_name == ""
        or type(replicas) is not int
        or replicas <= 0
        or template.get("RestartPolicy", {}).get("Condition")
        not in ("any", "on-failure")
    ):
        return None
    return scan_id


class WorkerRecovery:
    """Reconcile workers without restarting brokers or changing replica counts."""

    def __init__(self, docker_client: docker.DockerClient) -> None:
        self._docker_client = docker_client
        self._last_reconcile: float | None = None
        self._stalled_since: dict[str, float] = {}

    def reconcile(self, runner: scanner_runner.ScannerAPIRunner) -> None:
        """Check active local universes periodically, including when the scanner is full."""
        now = time.monotonic()
        if (
            self._last_reconcile is not None
            and now - self._last_reconcile < RECONCILE_INTERVAL_SECONDS
        ):
            return
        self._last_reconcile = now
        active = active_scan_ids(runner)
        if active is None or len(active) == 0:
            self._stalled_since.clear()
            return
        try:
            local_services = self._docker_client.services.list(
                filters={"label": "ostorlab.universe"}
            )
            for scan_id in active:
                workers = [
                    service
                    for service in local_services
                    if _worker_scan_id(service) == scan_id
                ]
                if len(workers) == 0:
                    continue
                brokers = [
                    service
                    for service in local_services
                    if service.attrs["Spec"].get("Labels", {}).get("ostorlab.universe")
                    == scan_id
                    and "ostorlab.mq" in service.attrs["Spec"].get("Labels", {})
                ]
                if len(brokers) != 1:
                    continue
                try:
                    queues = self._queues(brokers[0])
                    for worker in workers:
                        self._reconcile_worker(worker, scan_id, queues, runner, now)
                except (
                    docker.errors.DockerException,
                    container_exec.ExecError,
                    KeyError,
                    TypeError,
                    ValueError,
                ):
                    logger.exception(
                        "Cannot reconcile workers for scan %s; retaining services and queues.",
                        scan_id,
                    )
        except (docker.errors.DockerException, KeyError, TypeError):
            logger.exception("Cannot list local workers; skipping recovery.")

    def _queues(self, broker: services.Service) -> dict[str, dict[str, typing.Any]]:
        records = json.loads(
            container_exec.run(self._docker_client, broker, QUEUE_COMMAND)
        )
        if not isinstance(records, list):
            raise TypeError("invalid RabbitMQ queue response")
        queues = {}
        for record in records:
            name = record["name"]
            if not isinstance(name, str) or name in queues:
                raise ValueError("invalid RabbitMQ queue name")
            for field in ("messages_ready", "messages_unacknowledged", "consumers"):
                if type(record[field]) is not int or record[field] < 0:
                    raise ValueError(f"invalid RabbitMQ queue counter: {field}")
            queues[name] = record
        return queues

    def _reconcile_worker(
        self,
        worker: services.Service,
        scan_id: str,
        queues: dict[str, dict[str, typing.Any]],
        runner: scanner_runner.ScannerAPIRunner,
        now: float,
    ) -> None:
        worker.reload()
        if _worker_scan_id(worker) != scan_id:
            return
        labels = worker.attrs["Spec"]["Labels"]
        queue_name = f"{labels['ostorlab.queue_name']}_queue"
        failed_queue = queues.get(f"{queue_name}.failed")
        tasks = typing.cast(
            typing.Callable[[], list[dict[str, typing.Any]]], worker.tasks
        )()
        if (
            failed_queue is not None
            and failed_queue["messages_ready"] + failed_queue["messages_unacknowledged"]
            > 0
        ):
            self._report_error(
                runner,
                scan_id,
                worker,
                f"processing failed; inspect retained queue {queue_name}.failed",
                tasks,
            )
            return
        queue = queues.get(queue_name)
        running = sum(task["Status"]["State"] == "running" for task in tasks)
        orphaned_queue = (
            queue is not None
            and queue["messages_ready"] > 0
            and queue["consumers"] == 0
        )
        if running > 0 and orphaned_queue is False:
            self._stalled_since.pop(typing.cast(str, worker.id), None)
            return
        first_seen = self._stalled_since.setdefault(typing.cast(str, worker.id), now)
        if now - first_seen < STALL_GRACE_SECONDS:
            return
        attempts = int(labels.get(ATTEMPTS_LABEL, "0"))
        last_attempt = float(labels.get(LAST_ATTEMPT_LABEL, "0"))
        if time.time() - last_attempt < RECOVERY_COOLDOWN_SECONDS:
            return
        if attempts >= MAX_RECOVERY_ATTEMPTS:
            self._report_error(
                runner,
                scan_id,
                worker,
                "worker recovery exhausted; check task errors and memory capacity",
                tasks,
            )
            return
        active = active_scan_ids(runner)
        if active is None or scan_id not in active:
            return
        worker.reload()
        if _worker_scan_id(worker) != scan_id:
            return
        spec = worker.attrs["Spec"]
        labels = dict(spec["Labels"])
        if int(labels.get(ATTEMPTS_LABEL, "0")) != attempts:
            return
        labels[ATTEMPTS_LABEL] = str(attempts + 1)
        labels[LAST_ATTEMPT_LABEL] = str(time.time())
        typing.cast(typing.Callable[..., typing.Any], worker.update)(
            labels=labels, force_update=spec["TaskTemplate"].get("ForceUpdate", 0) + 1
        )
        logger.warning(
            "Restarted stalled worker %s of scan %s (attempt %s/%s); queues retained. Task status: %s",
            worker.name,
            scan_id,
            attempts + 1,
            MAX_RECOVERY_ATTEMPTS,
            [task["Status"] for task in tasks],
        )

    def _report_error(
        self,
        runner: scanner_runner.ScannerAPIRunner,
        scan_id: str,
        worker: services.Service,
        reason: str,
        tasks: list[dict[str, typing.Any]],
    ) -> None:
        active = active_scan_ids(runner)
        if active is None or scan_id not in active:
            return
        worker.reload()
        if _worker_scan_id(worker) != scan_id:
            return
        logger.error(
            "Scan %s worker %s: %s. Broker retained. Task status: %s",
            scan_id,
            worker.name,
            reason,
            [task["Status"] for task in tasks],
        )
        try:
            response = runner.execute(
                request=scan_update_state.ScanUpdateStateAPIRequest(
                    scan_id=int(scan_id), progress="error"
                )
            )
            data = response.get("data")
            update = data.get("updateScan") if isinstance(data, dict) else None
            if not isinstance(update, dict) or update.get("success") is not True:
                logger.error(
                    "API did not confirm error state for scan %s: %s", scan_id, response
                )
        except (base_runner.ResponseError, httpx.HTTPError):
            logger.exception("Failed to report worker failure for scan %s.", scan_id)
