"""Snapshot and restore of a scan universe state, used to pause and resume scans.

A paused scan keeps no resources on the scanner: its universe is torn down once its state is captured in a
snapshot. The state of a universe is held by two services:

- RabbitMQ: the pending agent messages, in one durable queue per agent.
- Redis: the agents persisted state, like deduplication sets and the tracker bookkeeping.

The snapshot is a gzip-compressed `UniverseSnapshot` protobuf message (see `proto/universe_snapshot.proto`) holding
the exchanges, the queues with their bindings and pending messages, and every Redis key. Message bodies, Redis keys
and Redis values are kept as raw bytes. The agents of the universe are stopped before the snapshot is taken, so their
unacknowledged messages are requeued and captured.

Restoring a snapshot runs inside the universe network before the agents start, see `main`.

Redis keys starting with `RUN_KEY_PREFIX` describe the current run of a universe, like when the tracker started
counting, and are not part of the snapshot: a resumed universe starts a new run.

The module only depends on the agent extra requirements (aio-pika, redis) when a snapshot is taken or restored.
"""

from __future__ import annotations

import argparse
import asyncio
import datetime
import gzip
import logging
import pathlib
import time
from typing import Any
from urllib import parse

import docker
import httpx
import tenacity
from docker import types as docker_types
from docker.models import services as docker_services
from google.protobuf import message as protobuf_message

from ostorlab.runtimes.local.proto import universe_snapshot_pb2

try:
    # Agent extra requirements: the scanner imports the module to restore snapshots without installing them, only the
    # snapshot taking and restoring code, run from agent images, uses them.
    import aio_pika
    import redis
except ImportError:
    aio_pika = None
    redis = None

logger = logging.getLogger(__name__)

SNAPSHOT_VERSION = 1
SNAPSHOT_FILENAME = "snapshot.pb.gz"
SNAPSHOT_MOUNT_PATH = "/snapshot"

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

# Messages are restored through a headers exchange matching on this header, so each message lands in the queue it
# was taken from while keeping its original routing key, which agents read as the message selector.
RESTORE_EXCHANGE = "ostorlab.snapshot.restore"
RESTORE_QUEUE_HEADER = "x-ostorlab-restore-queue"

STOP_AGENTS_TIMEOUT = datetime.timedelta(minutes=2)
STOP_AGENTS_CHECK_INTERVAL = datetime.timedelta(seconds=2)
MANAGEMENT_API_TIMEOUT = datetime.timedelta(seconds=30)
RESTORE_ATTEMPTS = 30
RESTORE_RETRY_WAIT = datetime.timedelta(seconds=2)


class Error(Exception):
    """Base error of the universe snapshot."""


class AgentsNotStoppedError(Error):
    """The agents of the universe did not stop in time."""


class InvalidSnapshotError(Error):
    """The snapshot document cannot be restored."""


class MissingAgentRequirementsError(Error):
    """The agent extra requirements are needed to take or restore a snapshot."""


def _check_agent_requirements() -> None:
    if aio_pika is None or redis is None:
        raise MissingAgentRequirementsError(
            "taking or restoring a snapshot requires the ostorlab[agent] extra requirements."
        )


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
        except (OSError, EOFError, protobuf_message.DecodeError) as e:
            raise InvalidSnapshotError(f"snapshot is not a gzip protobuf message: {e}")
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
    Run-once services, like the asset injection, are left alone: starting them again would run them twice.

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
    for service in _list_agent_services(docker_client, universe):
        if service.name in keep_services or _is_run_once_service(service) is True:
            continue
        labels = dict(service.attrs["Spec"].get("Labels") or {})
        stored_replicas = labels.get(REPLICAS_LABEL)
        if stored_replicas is not None:
            # Stopped by an earlier attempt, its replicas are already kept.
            stopped_services[service.name] = int(stored_replicas)
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
    while _has_active_tasks(docker_client, list(stopped_services)) is True:
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


def take_snapshot(
    universe: str,
    mq_url: str,
    mq_management_url: str,
    mq_vhost: str,
    redis_url: str,
) -> Snapshot:
    """Capture the pending messages and the Redis keys of a universe whose agents are stopped.

    Messages are read without acknowledgment and left in their queues, so the universe can resume when the pause is
    rolled back.

    Args:
        universe: Universe identifier.
        mq_url: AMQP URL of the universe RabbitMQ.
        mq_management_url: URL of the universe RabbitMQ management API.
        mq_vhost: RabbitMQ virtual host of the universe.
        redis_url: URL of the universe Redis.

    Returns:
        The universe snapshot.
    """
    _check_agent_requirements()
    # Kept for information: when the scan was paused, the agents being stopped already.
    paused_at_ms = int(time.time() * 1000)
    exchanges, queues = _list_mq_topology(mq_management_url, mq_vhost)
    asyncio.run(_read_queues_messages(mq_url, queues))
    snapshot = Snapshot(
        universe_snapshot_pb2.UniverseSnapshot(
            version=SNAPSHOT_VERSION,
            universe=universe,
            paused_at_ms=paused_at_ms,
            exchanges=exchanges,
            queues=queues,
            redis_keys=_dump_redis(redis_url),
        )
    )
    logger.info(
        "snapshot of universe %s: %s queues, %s messages, %s redis keys",
        universe,
        len(snapshot.proto.queues),
        snapshot.messages_count,
        len(snapshot.proto.redis_keys),
    )
    return snapshot


def restore_snapshot(snapshot: Snapshot, mq_url: str, redis_url: str) -> None:
    """Restore a snapshot in a universe whose agents are not started yet.

    Args:
        snapshot: The snapshot to restore.
        mq_url: AMQP URL of the universe RabbitMQ.
        redis_url: URL of the universe Redis.
    """
    _check_agent_requirements()
    _restore_redis(redis_url, snapshot)
    asyncio.run(_restore_mq(mq_url, snapshot))
    logger.info(
        "restored universe %s: %s queues, %s messages, %s redis keys",
        snapshot.universe,
        len(snapshot.proto.queues),
        snapshot.messages_count,
        len(snapshot.proto.redis_keys),
    )


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
        service = docker_client.services.get(service_name)
        for task in service.tasks():
            if task.get("Status", {}).get("State") not in FINAL_TASK_STATES:
                return True
    return False


def _list_mq_topology(
    mq_management_url: str, mq_vhost: str
) -> tuple[list[universe_snapshot_pb2.Exchange], list[universe_snapshot_pb2.Queue]]:
    """List the exchanges and the queues with their bindings using the RabbitMQ management API."""
    vhost = parse.quote(mq_vhost, safe="")
    with httpx.Client(
        base_url=mq_management_url, timeout=MANAGEMENT_API_TIMEOUT.total_seconds()
    ) as client:
        exchanges = [
            universe_snapshot_pb2.Exchange(
                name=exchange["name"],
                type=exchange["type"],
                durable=exchange["durable"],
                auto_delete=exchange["auto_delete"],
                arguments=_to_field_table(exchange.get("arguments") or {}),
            )
            for exchange in _get_json(client, f"api/exchanges/{vhost}")
            if exchange["name"] != "" and exchange["name"].startswith("amq.") is False
        ]
        queues = []
        for queue in _get_json(client, f"api/queues/{vhost}"):
            name = queue["name"]
            bindings = [
                universe_snapshot_pb2.Binding(
                    exchange=binding["source"],
                    routing_key=binding["routing_key"],
                    arguments=_to_field_table(binding.get("arguments") or {}),
                )
                for binding in _get_json(
                    client, f"api/queues/{vhost}/{parse.quote(name, safe='')}/bindings"
                )
                # The default exchange and the excluded amq.* exchanges are not captured, neither are their bindings.
                if binding["source"] != ""
                and binding["source"].startswith("amq.") is False
            ]
            queues.append(
                universe_snapshot_pb2.Queue(
                    name=name,
                    durable=queue["durable"],
                    arguments=_to_field_table(queue.get("arguments") or {}),
                    bindings=bindings,
                )
            )
    return exchanges, queues


def _get_json(client: httpx.Client, path: str) -> list[dict[str, Any]]:
    response = client.get(path)
    response.raise_for_status()
    return response.json()


async def _read_queues_messages(
    mq_url: str, queues: list[universe_snapshot_pb2.Queue]
) -> None:
    """Read every message of the queues without acknowledging them.

    The connection is closed once the messages are read, which puts the messages back in their queues.
    """
    connection = await aio_pika.connect(mq_url)
    try:
        channel = await connection.channel()
        for queue in queues:
            mq_queue = await channel.declare_queue(queue.name, passive=True)
            while True:
                message = await mq_queue.get(no_ack=False, fail=False)
                if message is None:
                    break
                queue.messages.append(_serialize_message(message))
    finally:
        await connection.close()


def _serialize_message(message: Any) -> universe_snapshot_pb2.Message:
    snapshot_message = universe_snapshot_pb2.Message(
        body=bytes(message.body),
        exchange=message.exchange or "",
        routing_key=message.routing_key or "",
        headers=_to_field_table(dict(message.headers or {})),
    )
    if message.priority is not None:
        snapshot_message.priority = message.priority
    if message.delivery_mode is not None:
        snapshot_message.delivery_mode = int(message.delivery_mode)
    for field in (
        "content_type",
        "content_encoding",
        "correlation_id",
        "message_id",
        "type",
        "app_id",
    ):
        value = getattr(message, field)
        if value is not None:
            setattr(snapshot_message, field, value)
    return snapshot_message


def _to_field_table(values: dict[str, Any]) -> universe_snapshot_pb2.FieldTable:
    table = universe_snapshot_pb2.FieldTable()
    for key, value in values.items():
        field_value = _to_field_value(value)
        if field_value is not None:
            table.fields[key].CopyFrom(field_value)
    return table


def _to_field_value(value: Any) -> universe_snapshot_pb2.FieldValue | None:
    """Convert an AMQP field value, values without a protobuf equivalent are kept as their string form."""
    if value is None:
        return None
    # bool is checked first, it is a subclass of int.
    if isinstance(value, bool):
        return universe_snapshot_pb2.FieldValue(bool_value=value)
    if isinstance(value, int):
        return universe_snapshot_pb2.FieldValue(int_value=value)
    if isinstance(value, float):
        return universe_snapshot_pb2.FieldValue(float_value=value)
    if isinstance(value, (bytes, bytearray)):
        return universe_snapshot_pb2.FieldValue(bytes_value=bytes(value))
    if isinstance(value, dict):
        return universe_snapshot_pb2.FieldValue(table_value=_to_field_table(value))
    if isinstance(value, (list, tuple)):
        array = universe_snapshot_pb2.FieldArray()
        for item in value:
            item_value = _to_field_value(item)
            if item_value is not None:
                array.values.append(item_value)
        return universe_snapshot_pb2.FieldValue(array_value=array)
    return universe_snapshot_pb2.FieldValue(string_value=str(value))


def _from_field_table(table: universe_snapshot_pb2.FieldTable) -> dict[str, Any]:
    return {key: _from_field_value(value) for key, value in table.fields.items()}


def _from_field_value(value: universe_snapshot_pb2.FieldValue) -> Any:
    kind = value.WhichOneof("value")
    if kind == "table_value":
        return _from_field_table(value.table_value)
    if kind == "array_value":
        return [_from_field_value(item) for item in value.array_value.values]
    if kind == "bytes_value":
        # AMQP field tables carry byte arrays as bytearray, plain bytes are rejected by the encoder.
        return bytearray(value.bytes_value)
    if kind is None:
        return None
    return getattr(value, kind)


def _dump_redis(redis_url: str) -> list[universe_snapshot_pb2.RedisKey]:
    keys = []
    with redis.Redis.from_url(redis_url) as client:
        for key in client.scan_iter(count=1000):
            if key.startswith(RUN_KEY_PREFIX) is True:
                continue
            value = client.dump(key)
            ttl_ms = client.pttl(key)
            if value is None or ttl_ms == -2:
                # The key expired between the scan and the dump.
                continue
            keys.append(
                universe_snapshot_pb2.RedisKey(
                    key=key, ttl_ms=max(ttl_ms, 0), value=value
                )
            )
    return keys


def _restore_redis(redis_url: str, snapshot: Snapshot) -> None:
    with redis.Redis.from_url(redis_url) as client:
        pipeline = client.pipeline(transaction=False)
        for redis_key in snapshot.proto.redis_keys:
            pipeline.restore(
                redis_key.key, redis_key.ttl_ms, redis_key.value, replace=True
            )
        pipeline.execute()


async def _restore_mq(mq_url: str, snapshot: Snapshot) -> None:
    connection = await aio_pika.connect(mq_url)
    try:
        channel = await connection.channel(publisher_confirms=True)
        exchanges = {}
        for exchange in snapshot.proto.exchanges:
            exchanges[exchange.name] = await channel.declare_exchange(
                exchange.name,
                type=exchange.type,
                durable=exchange.durable,
                auto_delete=exchange.auto_delete,
                arguments=_from_field_table(exchange.arguments),
            )
        restore_exchange = await channel.declare_exchange(
            RESTORE_EXCHANGE, type=aio_pika.ExchangeType.HEADERS, auto_delete=False
        )
        try:
            for queue in snapshot.proto.queues:
                mq_queue = await channel.declare_queue(
                    queue.name,
                    durable=queue.durable,
                    arguments=_from_field_table(queue.arguments),
                )
                for binding in queue.bindings:
                    exchange = exchanges.get(binding.exchange)
                    if exchange is None:
                        raise InvalidSnapshotError(
                            f"queue {queue.name} is bound to unknown exchange {binding.exchange}"
                        )
                    await mq_queue.bind(
                        exchange,
                        routing_key=binding.routing_key,
                        arguments=_from_field_table(binding.arguments),
                    )
                restore_binding = {"x-match": "all", RESTORE_QUEUE_HEADER: queue.name}
                await mq_queue.bind(restore_exchange, arguments=restore_binding)
                for message in queue.messages:
                    await restore_exchange.publish(
                        _build_message(message, queue_name=queue.name),
                        routing_key=message.routing_key,
                    )
                await mq_queue.unbind(restore_exchange, arguments=restore_binding)
        finally:
            await restore_exchange.delete()
    finally:
        await connection.close()


def _build_message(message: universe_snapshot_pb2.Message, queue_name: str) -> Any:
    headers = _from_field_table(message.headers)
    headers[RESTORE_QUEUE_HEADER] = queue_name
    optional_fields = {
        field: getattr(message, field)
        for field in (
            "priority",
            "delivery_mode",
            "content_type",
            "content_encoding",
            "correlation_id",
            "message_id",
            "type",
            "app_id",
        )
        if message.HasField(field) is True
    }
    return aio_pika.Message(body=message.body, headers=headers, **optional_fields)


def main(args: list[str] | None = None) -> None:
    """Restore a snapshot from inside the universe network, before the agents of the universe start."""
    parser = argparse.ArgumentParser(description=main.__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    restore_parser = subparsers.add_parser("restore")
    restore_parser.add_argument(
        "--snapshot",
        type=pathlib.Path,
        default=pathlib.Path(SNAPSHOT_MOUNT_PATH) / SNAPSHOT_FILENAME,
    )
    restore_parser.add_argument("--mq-url", required=True)
    restore_parser.add_argument("--redis-url", required=True)
    parsed_args = parser.parse_args(args)

    logging.basicConfig(level=logging.INFO)
    _check_agent_requirements()
    snapshot = Snapshot.from_bytes(parsed_args.snapshot.read_bytes())
    _wait_services_ready(mq_url=parsed_args.mq_url, redis_url=parsed_args.redis_url)
    # The restore runs once: retrying after a partial publish would duplicate messages.
    restore_snapshot(
        snapshot, mq_url=parsed_args.mq_url, redis_url=parsed_args.redis_url
    )


@tenacity.retry(
    stop=tenacity.stop_after_attempt(RESTORE_ATTEMPTS),
    wait=tenacity.wait_fixed(RESTORE_RETRY_WAIT.total_seconds()),
    reraise=True,
)
def _wait_services_ready(mq_url: str, redis_url: str) -> None:
    """Wait for the MQ and Redis services to accept connections, they report running before they do."""
    with redis.Redis.from_url(redis_url) as client:
        client.ping()
    asyncio.run(_check_mq_connection(mq_url))


async def _check_mq_connection(mq_url: str) -> None:
    connection = await aio_pika.connect(mq_url)
    await connection.close()


if __name__ == "__main__":
    main()
