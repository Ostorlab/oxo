"""Snapshot of the state of a scan universe, taken when its scan is paused and restored when it resumes.

The state of a universe lives in two services:

- RabbitMQ: the exchanges, the agent queues with their bindings and their pending messages.
- Redis: the agents persisted state, like deduplication sets and the tracker bookkeeping.

The stop scan agent takes the snapshot from inside the universe network once the other agents are stopped, and saves
it to `gs://<bucket>/<scan_id>`. When a scan starts, the local runtime looks its snapshot up: a paused scan has one and
is restored in the new MQ and Redis services before any agent starts, a new scan has none and starts from scratch.

A scan paused with `oxo scan pause` keeps its snapshot in a local file instead, see `save_file` and `load_file`.

The stored object is a gzip compressed JSON document. It is internal to this module: only `take`, `save`, `load`,
`save_file` and `load_file` read or write it.
"""

from __future__ import annotations

import base64
import dataclasses
import gzip
import json
import logging
import pathlib
import typing
from urllib import parse

import httpx
import redis
from google.api_core import exceptions as google_api_exceptions
from google.auth import exceptions as google_auth_exceptions
from google.cloud.storage import client as storage_client
from google.oauth2 import service_account

from ostorlab import exceptions
from ostorlab.runtimes import definitions

logger = logging.getLogger(__name__)

SNAPSHOT_VERSION = 1
MANAGEMENT_API_TIMEOUT_SECONDS = 60
# Upper bound of the messages read from a queue. The broker stops at the first empty read, the bound only guards
# against reading a queue that is still being filled.
MAX_QUEUE_MESSAGES = 1_000_000
EXCHANGE_FIELDS = ("name", "type", "durable", "auto_delete", "internal", "arguments")
QUEUE_FIELDS = ("name", "durable", "auto_delete", "arguments")


class Error(exceptions.OstorlabError):
    """Base error of the universe snapshots."""


class CaptureError(Error):
    """The state of the universe could not be captured."""


class StorageError(Error):
    """The snapshot could not be saved to or loaded from the bucket."""


class InvalidSnapshotError(Error):
    """The stored object is not a snapshot this module can restore."""


@dataclasses.dataclass(frozen=True)
class RedisKey:
    """A Redis key with its value serialized by `DUMP`, restored with `RESTORE`."""

    key: bytes
    # Remaining time to live in milliseconds, 0 for a key without expiration, as `RESTORE` expects.
    ttl_ms: int
    value: bytes


@dataclasses.dataclass(frozen=True)
class UniverseSnapshot:
    """State of a universe, as described by the RabbitMQ management API and Redis."""

    # Exchanges declared by the agents, with the fields the management API declares an exchange with.
    exchanges: list[dict[str, typing.Any]]
    # Queues with the fields the management API declares a queue with, their `bindings` and their pending
    # `messages`, as returned by the management API with a base64 payload.
    queues: list[dict[str, typing.Any]]
    redis_keys: list[RedisKey]


def object_name(scan_id: int | str) -> str:
    """Name of the snapshot object of a universe in the bucket.

    Args:
        scan_id: Scan id of the scanning engine, one per universe, also the name of the universe.
    """
    return str(scan_id)


def take(mq_management_url: str, mq_vhost: str, redis_url: str) -> UniverseSnapshot:
    """Capture the state of a universe whose agents are stopped.

    The messages are read and requeued, they stay in their queues: the universe can resume if the pause fails.

    Args:
        mq_management_url: URL of the RabbitMQ management API of the universe, with its credentials.
        mq_vhost: RabbitMQ virtual host of the universe.
        redis_url: URL of the Redis of the universe.

    Raises:
        CaptureError: When the MQ or Redis state cannot be read.
    """
    try:
        with httpx.Client(
            base_url=mq_management_url, timeout=MANAGEMENT_API_TIMEOUT_SECONDS
        ) as client:
            exchanges, queues = _read_mq(client, parse.quote(mq_vhost, safe=""))
        redis_keys = _dump_redis(redis_url)
    except (httpx.HTTPError, redis.RedisError, KeyError) as e:
        raise CaptureError(f"could not capture the universe state: {e}") from e
    logger.info(
        "captured %s exchanges, %s queues, %s messages, %s redis keys",
        len(exchanges),
        len(queues),
        sum(len(queue["messages"]) for queue in queues),
        len(redis_keys),
    )
    return UniverseSnapshot(exchanges=exchanges, queues=queues, redis_keys=redis_keys)


def save(
    settings: definitions.SnapshotSettings,
    key: str,
    universe_snapshot: UniverseSnapshot,
) -> None:
    """Store a snapshot in the bucket, replacing the previous snapshot of the universe.

    Args:
        settings: Bucket and service account of the snapshots.
        key: Object name, see `object_name`.
        universe_snapshot: The snapshot to store.

    Raises:
        StorageError: When the upload fails.
    """
    data = _pack(universe_snapshot)
    try:
        _bucket(settings).blob(key).upload_from_string(
            data, content_type="application/gzip"
        )
    except (
        google_api_exceptions.GoogleAPIError,
        google_auth_exceptions.GoogleAuthError,
    ) as e:
        raise StorageError(f"could not upload snapshot {key}: {e}") from e
    logger.info("saved snapshot %s, %s bytes", key, len(data))


def load(
    settings: definitions.SnapshotSettings, key: str
) -> typing.Optional[UniverseSnapshot]:
    """Fetch a snapshot from the bucket.

    Args:
        settings: Bucket and service account of the snapshots.
        key: Object name, see `object_name`.

    Returns:
        The snapshot, None when the universe has no snapshot.

    Raises:
        StorageError: When the download fails.
        InvalidSnapshotError: When the object is not a snapshot.
    """
    try:
        data = typing.cast(bytes, _bucket(settings).blob(key).download_as_bytes())
    except google_api_exceptions.NotFound:
        return None
    except (
        google_api_exceptions.GoogleAPIError,
        google_auth_exceptions.GoogleAuthError,
    ) as e:
        raise StorageError(f"could not download snapshot {key}: {e}") from e
    logger.info("loaded snapshot %s, %s bytes", key, len(data))
    return _unpack(data)


def save_file(path: pathlib.Path, universe_snapshot: UniverseSnapshot) -> None:
    """Store a snapshot in a local file, replacing the previous one.

    Args:
        path: Path of the file, its parent directories are created.
        universe_snapshot: The snapshot to store.

    Raises:
        StorageError: When the file cannot be written.
    """
    data = _pack(universe_snapshot)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    except OSError as e:
        raise StorageError(f"could not write snapshot {path}: {e}") from e
    logger.info("saved snapshot %s, %s bytes", path, len(data))


def load_file(path: pathlib.Path) -> typing.Optional[UniverseSnapshot]:
    """Read a snapshot from a local file.

    Args:
        path: Path of the file.

    Returns:
        The snapshot, None when the file does not exist.

    Raises:
        StorageError: When the file cannot be read.
        InvalidSnapshotError: When the file is not a snapshot.
    """
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        return None
    except OSError as e:
        raise StorageError(f"could not read snapshot {path}: {e}") from e
    logger.info("loaded snapshot %s, %s bytes", path, len(data))
    return _unpack(data)


def from_document(document: dict[str, typing.Any]) -> UniverseSnapshot:
    """Build a snapshot from its JSON document, the one stored without its version, with base64 Redis keys and values.

    Args:
        document: The `exchanges`, `queues` and `redis_keys` of the snapshot.

    Raises:
        InvalidSnapshotError: When the document is not a snapshot.
    """
    try:
        return UniverseSnapshot(
            exchanges=document["exchanges"],
            queues=document["queues"],
            redis_keys=[
                RedisKey(
                    key=base64.b64decode(redis_key["key"], validate=True),
                    ttl_ms=int(redis_key["ttl_ms"]),
                    value=base64.b64decode(redis_key["value"], validate=True),
                )
                for redis_key in document["redis_keys"]
            ],
        )
    # An invalid base64 value raises `ValueError`.
    except (ValueError, KeyError, TypeError) as e:
        raise InvalidSnapshotError(f"invalid snapshot: {e}") from e


def _bucket(settings: definitions.SnapshotSettings) -> typing.Any:
    try:
        credentials = typing.cast(
            typing.Callable[[typing.Any], service_account.Credentials],
            service_account.Credentials.from_service_account_info,
        )(json.loads(settings.service_account))
    # An invalid JSON document or a key missing a field, google-auth raises a `ValueError` for both.
    except ValueError as e:
        raise StorageError(f"invalid snapshot service account: {e}") from e
    # The project is taken from the key, the client otherwise looks it up in the environment.
    client = storage_client.Client(
        project=credentials.project_id, credentials=credentials
    )
    return client.bucket(settings.bucket.removeprefix("gs://"))


def _read_mq(
    client: httpx.Client, vhost: str
) -> tuple[list[dict[str, typing.Any]], list[dict[str, typing.Any]]]:
    exchanges = [
        {field: exchange[field] for field in EXCHANGE_FIELDS}
        for exchange in _get(client, f"api/exchanges/{vhost}")
        if _is_agent_exchange(exchange["name"]) is True
    ]
    queues = []
    for queue in _get(client, f"api/queues/{vhost}"):
        name = parse.quote(queue["name"], safe="")
        bindings = [
            {
                "source": binding["source"],
                "routing_key": binding["routing_key"],
                "arguments": binding["arguments"],
            }
            for binding in _get(client, f"api/queues/{vhost}/{name}/bindings")
            if _is_agent_exchange(binding["source"]) is True
        ]
        response = client.post(
            f"api/queues/{vhost}/{name}/get",
            json={
                "count": MAX_QUEUE_MESSAGES,
                # The messages are put back in the queue once read.
                "ackmode": "ack_requeue_true",
                "encoding": "base64",
            },
        )
        response.raise_for_status()
        messages = [
            {
                "routing_key": message["routing_key"],
                # The management API returns an empty list for a message without properties.
                "properties": message["properties"] or {},
                "payload": message["payload"],
                "payload_encoding": message["payload_encoding"],
            }
            for message in response.json()
        ]
        if len(messages) >= MAX_QUEUE_MESSAGES:
            raise CaptureError(
                f"queue {queue['name']} holds more than {MAX_QUEUE_MESSAGES} messages."
            )
        queues.append(
            {field: queue[field] for field in QUEUE_FIELDS}
            | {"bindings": bindings, "messages": messages}
        )
    return exchanges, queues


def _get(client: httpx.Client, path: str) -> list[dict[str, typing.Any]]:
    response = client.get(path)
    response.raise_for_status()
    return typing.cast(list[dict[str, typing.Any]], response.json())


def _is_agent_exchange(name: str) -> bool:
    """The default exchange and the `amq.*` exchanges exist in every broker, they are not captured."""
    return name != "" and name.startswith("amq.") is False


def _dump_redis(redis_url: str) -> list[RedisKey]:
    keys = []
    with redis.Redis.from_url(redis_url) as client:
        for key in client.scan_iter(count=1000):
            value = client.dump(key)
            ttl_ms = client.pttl(key)
            if value is None or ttl_ms == -2:
                # The key expired between the scan and the dump.
                continue
            keys.append(RedisKey(key=key, ttl_ms=max(ttl_ms, 0), value=value))
    return keys


def _pack(universe_snapshot: UniverseSnapshot) -> bytes:
    document = {
        "version": SNAPSHOT_VERSION,
        "exchanges": universe_snapshot.exchanges,
        "queues": universe_snapshot.queues,
        "redis_keys": [
            {
                "key": base64.b64encode(redis_key.key).decode(),
                "ttl_ms": redis_key.ttl_ms,
                "value": base64.b64encode(redis_key.value).decode(),
            }
            for redis_key in universe_snapshot.redis_keys
        ],
    }
    return gzip.compress(json.dumps(document).encode())


def _unpack(data: bytes) -> UniverseSnapshot:
    try:
        document = json.loads(gzip.decompress(data))
        version = document["version"]
    # A corrupted gzip stream raises `OSError` or `EOFError`, an invalid JSON document `ValueError`.
    except (OSError, EOFError, ValueError, KeyError, TypeError) as e:
        raise InvalidSnapshotError(f"invalid snapshot: {e}") from e
    if version != SNAPSHOT_VERSION:
        raise InvalidSnapshotError(f"unsupported snapshot version {version}.")
    return from_document(document)
