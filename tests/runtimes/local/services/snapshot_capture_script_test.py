"""Unit tests for the script capturing the MQ and Redis state inside the MQ container."""

import io
import json
import pathlib
import typing

import pytest
from pytest_mock import plugin

from ostorlab.runtimes.local import snapshot
from ostorlab.runtimes.local.services import snapshot_capture_script

EXCHANGE = {
    "name": "ostorlab_topic_1",
    "type": "topic",
    "durable": False,
    "auto_delete": False,
    "internal": False,
    "arguments": {},
    "vhost": "/",
}
QUEUE = {
    "name": "nmap",
    "durable": True,
    "auto_delete": False,
    "arguments": {"x-max-priority": 3},
    "messages": 1,
}
MESSAGE = {
    "routing_key": "v3.asset.ip.v4",
    "properties": {"priority": 1},
    "payload": "AG1lc3NhZ2U=",
    "payload_encoding": "base64",
    "redelivered": False,
}


def _management_api(path: str) -> typing.Any:
    responses: dict[str, typing.Any] = {
        "exchanges/%2F": [
            EXCHANGE,
            {"name": "", "type": "direct"},
            {"name": "amq.topic", "type": "topic"},
        ],
        "queues/%2F": [QUEUE],
        "queues/%2F/nmap/bindings": [
            {"source": "", "routing_key": "nmap", "arguments": {}},
            {"source": "ostorlab_topic_1", "routing_key": "v3.#", "arguments": {}},
        ],
        "queues/%2F/nmap/get": [MESSAGE],
    }
    return responses[path]


class FakeRedis:
    """Redis connection answering the commands of the capture from a fixed keyspace, over two scan pages."""

    def __init__(self, keys: dict[bytes, tuple[bytes | None, int]]) -> None:
        self._keys = keys

    def command(self, *args: bytes) -> typing.Any:
        if args[0] == b"SCAN":
            names = list(self._keys)
            if args[1] == b"0":
                return [b"1", names[:1]]
            return [b"0", names[1:]]
        value, ttl_ms = self._keys[args[1]]
        return value if args[0] == b"DUMP" else ttl_ms


def testCaptureMq_always_capturesAgentExchangesQueuesBindingsAndMessages(
    mocker: plugin.MockerFixture,
) -> None:
    """The default and `amq.*` exchanges are skipped, the messages are read and requeued."""
    call = mocker.patch.object(
        snapshot_capture_script,
        "call",
        side_effect=lambda method, path, body=None: _management_api(path),
    )

    exchanges, queues = snapshot_capture_script.capture_mq("/")

    assert exchanges == [
        {key: value for key, value in EXCHANGE.items() if key != "vhost"}
    ]
    assert queues == [
        {
            "name": "nmap",
            "durable": True,
            "auto_delete": False,
            "arguments": {"x-max-priority": 3},
            "bindings": [
                {"source": "ostorlab_topic_1", "routing_key": "v3.#", "arguments": {}}
            ],
            "messages": [
                {
                    "routing_key": "v3.asset.ip.v4",
                    "properties": {"priority": 1},
                    "payload": "AG1lc3NhZ2U=",
                    "payload_encoding": "base64",
                }
            ],
        }
    ]
    get_body = call.call_args_list[-1].args[2]
    assert get_body["ackmode"] == "ack_requeue_true"


def testCaptureRedis_always_dumpsEveryKeyOfEveryScanPage() -> None:
    """Every key is dumped with its time to live, a key without expiration has a time to live of 0."""
    connection = FakeRedis(
        {b"\xffkey": (b"\x00dump", -1), b"scan_remaining_seconds": (b"\x00ttl", 5000)}
    )

    keys = snapshot_capture_script.capture_redis(
        typing.cast(snapshot_capture_script.RedisConnection, connection)
    )

    assert keys == [
        {"key": "/2tleQ==", "ttl_ms": 0, "value": "AGR1bXA="},
        {
            "key": "c2Nhbl9yZW1haW5pbmdfc2Vjb25kcw==",
            "ttl_ms": 5000,
            "value": "AHR0bA==",
        },
    ]


def testCaptureRedis_whenKeyExpiresDuringCapture_skipsKey() -> None:
    """A key that expired between the scan and the dump is not captured."""
    connection = FakeRedis({b"a": (None, -2), b"b": (b"\x00b", -1)})

    keys = snapshot_capture_script.capture_redis(
        typing.cast(snapshot_capture_script.RedisConnection, connection)
    )

    assert [key["key"] for key in keys] == ["Yg=="]


def testRedisConnectionCommand_always_sendsTheCommandAndDecodesTheReply(
    mocker: plugin.MockerFixture,
) -> None:
    """Commands are sent with the Redis protocol, bulk strings, integers and arrays are decoded."""
    sock = mocker.MagicMock()
    sock.makefile.return_value = io.BytesIO(
        b"*2\r\n$1\r\n0\r\n*1\r\n$1\r\nk\r\n:-1\r\n$-1\r\n"
    )
    mocker.patch("socket.create_connection", return_value=sock)
    connection = snapshot_capture_script.RedisConnection("redis_7")

    assert connection.command(b"SCAN", b"0") == [b"0", [b"k"]]
    assert connection.command(b"PTTL", b"k") == -1
    assert connection.command(b"DUMP", b"missing") is None
    assert sock.sendall.call_args_list[0].args[0] == b"*2\r\n$4\r\nSCAN\r\n$1\r\n0\r\n"


def testRedisConnectionCommand_whenRedisAnswersAnError_raisesRedisError(
    mocker: plugin.MockerFixture,
) -> None:
    """An error reply is raised, the capture fails instead of missing keys."""
    sock = mocker.MagicMock()
    sock.makefile.return_value = io.BytesIO(b"-ERR unknown command\r\n")
    mocker.patch("socket.create_connection", return_value=sock)
    connection = snapshot_capture_script.RedisConnection("redis_7")

    with pytest.raises(snapshot_capture_script.RedisError, match="unknown command"):
        connection.command(b"DUMP", b"k")


def testMain_always_writesAStateTheSnapshotCanRead(
    mocker: plugin.MockerFixture, tmp_path: pathlib.Path
) -> None:
    """The written state is the document of a snapshot."""
    mocker.patch.object(
        snapshot_capture_script,
        "call",
        side_effect=lambda method, path, body=None: _management_api(path),
    )
    connection = mocker.MagicMock()
    connection.command.side_effect = FakeRedis({b"k": (b"\x00v", -1)}).command
    mocker.patch.object(
        snapshot_capture_script, "RedisConnection", return_value=connection
    )
    output = tmp_path / "state.json"

    status = snapshot_capture_script.main(["script", "/", "redis_7", str(output)])

    assert status == 0
    universe_snapshot = snapshot.from_document(json.loads(output.read_text()))
    assert universe_snapshot.redis_keys == [
        snapshot.RedisKey(key=b"k", ttl_ms=0, value=b"\x00v")
    ]
    assert [queue["name"] for queue in universe_snapshot.queues] == ["nmap"]
    connection.close.assert_called_once()
