"""Unit tests for the universe snapshots."""

import base64
import gzip
import json
import typing
from unittest import mock

import pytest
import pytest_httpx
from google.api_core import exceptions as google_api_exceptions
from google.oauth2 import service_account
from pytest_mock import plugin

from ostorlab.runtimes import definitions
from ostorlab.runtimes.local import snapshot

MANAGEMENT_URL = "http://mq_1:15672/"
SETTINGS = definitions.SnapshotSettings(
    bucket="gs://scan-snapshots",
    service_account=b'{"type": "service_account", "project_id": "project"}',
)
UNIVERSE_SNAPSHOT = snapshot.UniverseSnapshot(
    exchanges=[
        {
            "name": "ostorlab_topic_1",
            "type": "topic",
            "durable": False,
            "auto_delete": False,
            "internal": False,
            "arguments": {"x-max-length": 10000},
        }
    ],
    queues=[
        {
            "name": "nmap",
            "durable": True,
            "auto_delete": False,
            "arguments": {"x-max-priority": 3},
            "bindings": [
                {
                    "source": "ostorlab_topic_1",
                    "routing_key": "v3.asset.ip.#",
                    "arguments": {},
                }
            ],
            "messages": [
                {
                    "routing_key": "v3.asset.ip.v4",
                    "properties": {"priority": 1},
                    "payload": base64.b64encode(b"\x00message").decode(),
                    "payload_encoding": "base64",
                }
            ],
        }
    ],
    redis_keys=[snapshot.RedisKey(key=b"\xffkey", ttl_ms=0, value=b"\x00value")],
)


def _mock_redis(mocker: plugin.MockerFixture, keys: list[bytes]) -> mock.MagicMock:
    client: mock.MagicMock = mocker.MagicMock()
    client.scan_iter.return_value = keys
    client.dump.side_effect = lambda key: b"dump:" + key
    client.pttl.return_value = -1
    from_url = mocker.patch("redis.Redis.from_url")
    from_url.return_value.__enter__.return_value = client
    return client


def _google_api_error(error_class: type[Exception]) -> Exception:
    """Build a google-api-core error, its constructor is untyped."""
    return typing.cast(typing.Callable[[str], Exception], error_class)("error")


def _mock_bucket(mocker: plugin.MockerFixture) -> mock.MagicMock:
    mocker.patch.object(service_account.Credentials, "from_service_account_info")
    storage_client = mocker.patch("google.cloud.storage.client.Client")
    return typing.cast(mock.MagicMock, storage_client.return_value.bucket)


def testTake_whenUniverseHasMessagesAndKeys_capturesMqAndRedisState(
    mocker: plugin.MockerFixture, httpx_mock: pytest_httpx.HTTPXMock
) -> None:
    """Agent exchanges, queues, bindings and messages are captured with the Redis keys of the universe."""
    httpx_mock.add_response(
        url=f"{MANAGEMENT_URL}api/exchanges/%2F",
        json=[
            {
                "name": "",
                "type": "direct",
                "durable": True,
                "auto_delete": False,
                "internal": False,
                "arguments": {},
            },
            {
                "name": "amq.topic",
                "type": "topic",
                "durable": True,
                "auto_delete": False,
                "internal": False,
                "arguments": {},
            },
            UNIVERSE_SNAPSHOT.exchanges[0] | {"vhost": "/"},
        ],
    )
    httpx_mock.add_response(
        url=f"{MANAGEMENT_URL}api/queues/%2F",
        json=[
            {
                "name": "nmap",
                "durable": True,
                "auto_delete": False,
                "arguments": {"x-max-priority": 3},
                "messages": 1,
            }
        ],
    )
    httpx_mock.add_response(
        url=f"{MANAGEMENT_URL}api/queues/%2F/nmap/bindings",
        json=[
            {"source": "", "routing_key": "nmap", "arguments": {}},
            {
                "source": "ostorlab_topic_1",
                "routing_key": "v3.asset.ip.#",
                "arguments": {},
                "destination": "nmap",
            },
        ],
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{MANAGEMENT_URL}api/queues/%2F/nmap/get",
        json=[
            {
                "routing_key": "v3.asset.ip.v4",
                "exchange": "ostorlab_topic_1",
                "redelivered": True,
                "properties": {"priority": 1},
                "payload": base64.b64encode(b"\x00message").decode(),
                "payload_encoding": "base64",
            }
        ],
    )
    _mock_redis(mocker, keys=[b"ostorlab:run:start", b"\xffkey"])

    universe_snapshot = snapshot.take(MANAGEMENT_URL, "/", "redis://redis_1:6379/")

    assert universe_snapshot.exchanges == UNIVERSE_SNAPSHOT.exchanges
    assert universe_snapshot.queues == UNIVERSE_SNAPSHOT.queues
    assert universe_snapshot.redis_keys == [
        snapshot.RedisKey(key=b"\xffkey", ttl_ms=0, value=b"dump:\xffkey")
    ]
    get_request = httpx_mock.get_requests(method="POST")[0]
    assert json.loads(get_request.content)["ackmode"] == "ack_requeue_true"


def testTake_whenMessageHasNoProperties_capturesEmptyProperties(
    mocker: plugin.MockerFixture, httpx_mock: pytest_httpx.HTTPXMock
) -> None:
    """The management API lists missing properties as an empty list, they are restored as an object."""
    httpx_mock.add_response(url=f"{MANAGEMENT_URL}api/exchanges/%2F", json=[])
    httpx_mock.add_response(
        url=f"{MANAGEMENT_URL}api/queues/%2F",
        json=[{"name": "nmap", "durable": True, "auto_delete": False, "arguments": {}}],
    )
    httpx_mock.add_response(
        url=f"{MANAGEMENT_URL}api/queues/%2F/nmap/bindings", json=[]
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{MANAGEMENT_URL}api/queues/%2F/nmap/get",
        json=[
            {
                "routing_key": "v3.asset.ip.v4",
                "properties": [],
                "payload": "",
                "payload_encoding": "base64",
            }
        ],
    )
    _mock_redis(mocker, keys=[])

    universe_snapshot = snapshot.take(MANAGEMENT_URL, "/", "redis://redis_1:6379/")

    assert universe_snapshot.queues[0]["messages"][0]["properties"] == {}


def testTake_whenRedisKeyExpiresDuringCapture_skipsKey(
    mocker: plugin.MockerFixture, httpx_mock: pytest_httpx.HTTPXMock
) -> None:
    """A key gone between the scan and the dump is not captured."""
    httpx_mock.add_response(url=f"{MANAGEMENT_URL}api/exchanges/%2F", json=[])
    httpx_mock.add_response(url=f"{MANAGEMENT_URL}api/queues/%2F", json=[])
    client = _mock_redis(mocker, keys=[b"expired"])
    client.dump.side_effect = None
    client.dump.return_value = None

    universe_snapshot = snapshot.take(MANAGEMENT_URL, "/", "redis://redis_1:6379/")

    assert universe_snapshot.redis_keys == []


def testTake_whenManagementApiFails_raisesCaptureError(
    httpx_mock: pytest_httpx.HTTPXMock,
) -> None:
    """A failing management API call fails the capture."""
    httpx_mock.add_response(url=f"{MANAGEMENT_URL}api/exchanges/%2F", status_code=500)

    with pytest.raises(snapshot.CaptureError):
        snapshot.take(MANAGEMENT_URL, "/", "redis://redis_1:6379/")


def testObjectName_always_returnsScanId() -> None:
    """The snapshot of a universe is stored under its scanning engine scan id, one object per universe."""
    assert snapshot.object_name(scan_id=7) == "7"


def testSaveThenLoad_always_returnsTheSavedSnapshot(
    mocker: plugin.MockerFixture,
) -> None:
    """A saved snapshot is uploaded to its object and loads back identical, binary values included."""
    bucket = _mock_bucket(mocker)

    snapshot.save(SETTINGS, "7", UNIVERSE_SNAPSHOT)
    blob = bucket.return_value.blob.return_value
    uploaded = blob.upload_from_string.call_args.args[0]
    blob.download_as_bytes.return_value = uploaded
    loaded = snapshot.load(SETTINGS, "7")

    bucket.assert_called_with("scan-snapshots")
    bucket.return_value.blob.assert_called_with("7")
    assert loaded == UNIVERSE_SNAPSHOT


def testLoad_whenObjectIsMissing_returnsNone(
    mocker: plugin.MockerFixture,
) -> None:
    """A universe that was never paused has no snapshot."""
    bucket = _mock_bucket(mocker)
    bucket.return_value.blob.return_value.download_as_bytes.side_effect = (
        _google_api_error(google_api_exceptions.NotFound)
    )

    assert snapshot.load(SETTINGS, "7") is None


def testLoad_whenDownloadFails_raisesStorageError(
    mocker: plugin.MockerFixture,
) -> None:
    """A failed download is not mistaken for a missing snapshot."""
    bucket = _mock_bucket(mocker)
    bucket.return_value.blob.return_value.download_as_bytes.side_effect = (
        _google_api_error(google_api_exceptions.Forbidden)
    )

    with pytest.raises(snapshot.StorageError):
        snapshot.load(SETTINGS, "7")


def testLoad_whenServiceAccountIsInvalid_raisesStorageError() -> None:
    """A service account that is not a JSON key is reported as a storage error."""
    settings = definitions.SnapshotSettings(
        bucket="scan-snapshots", service_account=b"not json"
    )

    with pytest.raises(snapshot.StorageError):
        snapshot.load(settings, "7")


@pytest.mark.parametrize(
    "data",
    [
        b"not gzip",
        gzip.compress(b"not json"),
        gzip.compress(json.dumps({"version": 2}).encode()),
        gzip.compress(json.dumps({"version": 1}).encode()),
    ],
)
def testLoad_whenObjectIsNotASnapshot_raisesInvalidSnapshotError(
    mocker: plugin.MockerFixture, data: bytes
) -> None:
    """A corrupted or unknown object is never restored."""
    bucket = _mock_bucket(mocker)
    bucket.return_value.blob.return_value.download_as_bytes.return_value = data

    with pytest.raises(snapshot.InvalidSnapshotError):
        snapshot.load(SETTINGS, "7")


def testSave_whenUploadFails_raisesStorageError(
    mocker: plugin.MockerFixture,
) -> None:
    """A failed upload fails the pause."""
    bucket = _mock_bucket(mocker)
    bucket.return_value.blob.return_value.upload_from_string.side_effect = (
        _google_api_error(google_api_exceptions.Forbidden)
    )

    with pytest.raises(snapshot.StorageError):
        snapshot.save(SETTINGS, "7", UNIVERSE_SNAPSHOT)
