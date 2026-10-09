"""Snapshot of a scan universe state, used to pause and resume scans.

A paused scan keeps no resources on the scanner: its universe is torn down once its state is captured in a
snapshot. The state of a universe is held by two services:

- RabbitMQ: the pending agent messages, in one durable queue per agent.
- Redis: the agents persisted state, like deduplication sets and the tracker bookkeeping.

The snapshot is a gzip-compressed `UniverseSnapshot` protobuf message (see `runtimes/proto/universe_snapshot.proto`)
holding the exchanges, the queues with their bindings and pending messages, and the Redis keys. Message bodies, Redis
keys and Redis values are kept as raw bytes. The agents of the universe are stopped before the snapshot is taken, so their
unacknowledged messages are requeued and captured.

This module holds the snapshot format and the stop and start of the agents, it only needs the core requirements.
Taking and restoring the RabbitMQ and Redis state needs the agent requirements and lives in `snapshot_state`.

Redis keys starting with `RUN_KEY_PREFIX` describe the current run of a universe, like when the tracker started
counting, and are not part of the snapshot: a resumed universe starts a new run.
"""

from __future__ import annotations

import datetime
import gzip
import logging
import time
import zlib

import docker
from docker import errors as docker_errors
from docker import types as docker_types
from docker.models import services as docker_services
from google.protobuf import message as protobuf_message

from ostorlab import exceptions
from ostorlab.runtimes.proto import universe_snapshot_pb2

logger = logging.getLogger(__name__)

SNAPSHOT_VERSION = 1
SNAPSHOT_FILENAME = "snapshot.pb.gz"
SNAPSHOT_MOUNT_PATH = "/snapshot"
# Module run by the restore container: `python3 -m <RESTORE_MODULE> restore`.
RESTORE_MODULE = "ostorlab.runtimes.local.snapshot_state"

# Redis keys of the current run of a universe, left out of the snapshot.
RUN_KEY_PREFIX = b"ostorlab:run:"

UNIVERSE_LABEL = "ostorlab.universe"
# Only agent services carry the queue name label, the MQ and Redis services of the universe do not.
AGENT_SERVICE_LABEL = "ostorlab.queue_name"
# Docker task states a task never leaves: the task no longer runs and will not run again.
FINAL_TASK_STATES = frozenset(
    {"complete", "shutdown", "failed", "rejected", "orphaned", "remove"}
)
REPLICAS_LABEL = "ostorlab.snapshot.replicas"

STOP_AGENTS_TIMEOUT = datetime.timedelta(minutes=2)
STOP_AGENTS_CHECK_INTERVAL = datetime.timedelta(seconds=2)


class Error(exceptions.OstorlabError):
    """Base error of the universe snapshot."""


class AgentsNotStoppedError(Error):
    """The agents of the universe did not stop in time."""


class InvalidSnapshotError(Error):
    """The snapshot document cannot be restored."""


class Snapshot:
    """State of a universe captured when its scan is paused."""

    def __init__(self, proto: universe_snapshot_pb2.UniverseSnapshot) -> None:
        self.proto = proto

    @property
    def universe(self) -> str:
        return self.proto.universe

    @property
    def paused_at(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(
            self.proto.paused_at_ms / 1000, tz=datetime.timezone.utc
        )

    @property
    def messages_count(self) -> int:
        return sum(len(queue.messages) for queue in self.proto.queues)

    def to_bytes(self) -> bytes:
        return gzip.compress(self.proto.SerializeToString())

    @classmethod
    def from_bytes(cls, data: bytes) -> Snapshot:
        try:
            proto = universe_snapshot_pb2.UniverseSnapshot.FromString(
                gzip.decompress(data)
            )
        except (OSError, EOFError, zlib.error, protobuf_message.DecodeError) as e:
            raise InvalidSnapshotError(
                f"snapshot is not a gzip protobuf message: {e}"
            ) from e
        if proto.version != SNAPSHOT_VERSION:
            raise InvalidSnapshotError(f"unsupported snapshot version {proto.version}")
        return cls(proto)


def stop_universe_agents(
    docker_client: docker.DockerClient,
    universe: str,
    keep_services: set[str] | None = None,
    timeout: datetime.timedelta = STOP_AGENTS_TIMEOUT,
) -> dict[str, int]:
    """Scale the agent services of the universe to zero replicas and wait for their tasks to stop.

    Stopping an agent requeues the message it was processing, so the snapshot captures it. The replicas of each
    service are kept in its `REPLICAS_LABEL` label, so `start_universe_agents` can start the agents again even when
    this call fails midway, and a later attempt keeps the replicas of the agents an earlier attempt stopped.
    Run-once services, like the asset injection, are not scaled: starting them again would run them twice. Their tasks
    are still waited for, so they finish publishing before the queues are read.

    Args:
        docker_client: Docker client of the swarm running the universe.
        universe: Universe identifier.
        keep_services: Names of agent services to keep running, like the agent taking the snapshot.
        timeout: Maximum time to wait for the agent tasks to stop.

    Returns:
        The replicas of every stopped service.

    Raises:
        AgentsNotStoppedError: When agent tasks are still running after the timeout.
    """
    keep_services = keep_services or set()
    stopped_services: dict[str, int] = {}
    # Every agent may still publish or consume while the snapshot is taken, including run-once services and services
    # already scaled to zero whose tasks are still stopping: the snapshot waits for all of them.
    waited_services: list[str] = []
    for service in _list_agent_services(docker_client, universe):
        if service.name in keep_services:
            continue
        waited_services.append(service.name)
        if _is_run_once_service(service) is True:
            continue
        labels = dict(service.attrs["Spec"].get("Labels") or {})
        stored_replicas = labels.get(REPLICAS_LABEL)
        if stored_replicas is not None:
            # Stopped by an earlier attempt, its replicas are already kept. It is scaled down again when something
            # started it since, the stored replicas stay the ones it had before the first attempt.
            stopped_services[service.name] = int(stored_replicas)
            if _service_replicas(service) > 0:
                service.update(
                    mode=docker_types.ServiceMode("replicated", replicas=0),
                    labels=labels,
                )
            continue
        replicas = _service_replicas(service)
        if replicas == 0:
            continue
        logger.info("stopping agent service %s (%s replicas)", service.name, replicas)
        service.update(
            mode=docker_types.ServiceMode("replicated", replicas=0),
            labels=labels | {REPLICAS_LABEL: str(replicas)},
        )
        stopped_services[service.name] = replicas

    deadline = time.monotonic() + timeout.total_seconds()
    while _has_active_tasks(docker_client, waited_services) is True:
        if time.monotonic() > deadline:
            raise AgentsNotStoppedError(
                f"agents of universe {universe} still running after {timeout}."
            )
        time.sleep(STOP_AGENTS_CHECK_INTERVAL.total_seconds())
    return stopped_services


def start_universe_agents(docker_client: docker.DockerClient, universe: str) -> None:
    """Scale the agent services stopped by `stop_universe_agents` back to their replicas, to roll back a failed pause.

    Services already started again carry no `REPLICAS_LABEL` label, so the call can be repeated.
    """
    for service in _list_agent_services(docker_client, universe):
        labels = dict(service.attrs["Spec"].get("Labels") or {})
        stored_replicas = labels.pop(REPLICAS_LABEL, None)
        if stored_replicas is None:
            continue
        logger.info(
            "starting agent service %s again (%s replicas)",
            service.name,
            stored_replicas,
        )
        service.update(
            mode=docker_types.ServiceMode("replicated", replicas=int(stored_replicas)),
            labels=labels,
        )


def _is_run_once_service(service: docker_services.Service) -> bool:
    restart_policy = service.attrs["Spec"]["TaskTemplate"].get("RestartPolicy") or {}
    return restart_policy.get("Condition") == "none"


def _list_agent_services(
    docker_client: docker.DockerClient, universe: str
) -> list[docker_services.Service]:
    return docker_client.services.list(
        filters={"label": [f"{UNIVERSE_LABEL}={universe}", AGENT_SERVICE_LABEL]}
    )


def _service_replicas(service: docker_services.Service) -> int:
    mode = service.attrs.get("Spec", {}).get("Mode", {})
    return int((mode.get("Replicated") or {}).get("Replicas", 0))


def _has_active_tasks(
    docker_client: docker.DockerClient, service_names: list[str]
) -> bool:
    """Whether a task of the services is not in a final state.

    A task still pending, assigned or preparing can become running and consume messages while the snapshot is taken,
    so only the final states count as stopped.
    """
    for service_name in service_names:
        try:
            service = docker_client.services.get(service_name)
        except docker_errors.NotFound:
            # A service removed while waiting, like a finished run-once service, has no task left.
            continue
        for task in service.tasks():
            if task.get("Status", {}).get("State") not in FINAL_TASK_STATES:
                return True
    return False
