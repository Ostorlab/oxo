"""Capture the MQ and Redis state of a universe whose agents are stopped, run with python3 inside the MQ container.

`LocalRabbitMQ.capture` copies this script to the container, runs it, then reads the state it writes. Like the restore
script, it only uses the standard library of the python3 shipped with the RabbitMQ management image: it talks to the
management API on localhost, and to the Redis of the universe through its network address with the Redis protocol.

The written state is the JSON document of `snapshot.from_document`, the same as `snapshot.take` captures from inside
the universe network.
"""

from __future__ import annotations

import base64
import json
import socket
import sys
import typing
from urllib import parse
from urllib import request

MANAGEMENT_API_URL = "http://localhost:15672/api"
CREDENTIALS = base64.b64encode(b"guest:guest").decode()
REQUEST_TIMEOUT_SECONDS = 60
# Upper bound of the messages read from a queue, see `snapshot.MAX_QUEUE_MESSAGES`.
MAX_QUEUE_MESSAGES = 1_000_000
EXCHANGE_FIELDS = ("name", "type", "durable", "auto_delete", "internal", "arguments")
QUEUE_FIELDS = ("name", "durable", "auto_delete", "arguments")
REDIS_PORT = 6379
REDIS_SCAN_COUNT = b"1000"


class Error(Exception):
    """Base error of the capture script."""


class CaptureError(Error):
    """The state of the universe could not be captured."""


class RedisError(Error):
    """Redis answered a command with an error."""


def call(method: str, path: str, body: typing.Any = None) -> typing.Any:
    """Call the management API and return the decoded JSON response."""
    api_request = request.Request(
        f"{MANAGEMENT_API_URL}/{path}",
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Authorization": f"Basic {CREDENTIALS}",
            "Content-Type": "application/json",
        },
    )
    with request.urlopen(api_request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        return json.loads(response.read())


class RedisConnection:
    """Minimal Redis client, the RabbitMQ image has no Redis library."""

    def __init__(self, host: str, port: int = REDIS_PORT) -> None:
        self._socket = socket.create_connection(
            (host, port), timeout=REQUEST_TIMEOUT_SECONDS
        )
        self._reader = self._socket.makefile("rb")

    def close(self) -> None:
        self._reader.close()
        self._socket.close()

    def command(self, *args: bytes) -> typing.Any:
        """Send a command and return its decoded reply."""
        self._socket.sendall(
            b"*%d\r\n" % len(args)
            + b"".join(b"$%d\r\n%s\r\n" % (len(arg), arg) for arg in args)
        )
        return self._read_reply()

    def _read_reply(self) -> typing.Any:
        line = self._reader.readline()
        if line.endswith(b"\r\n") is False:
            raise RedisError("connection closed.")
        prefix, content = line[:1], line[1:-2]
        if prefix == b"+":
            return content
        if prefix == b"-":
            raise RedisError(content.decode(errors="replace"))
        if prefix == b":":
            return int(content)
        if prefix == b"$":
            length = int(content)
            if length == -1:
                return None
            return self._reader.read(length + 2)[:-2]
        if prefix == b"*":
            length = int(content)
            if length == -1:
                return None
            return [self._read_reply() for _ in range(length)]
        raise RedisError(f"unexpected reply {line!r}.")


def capture_mq(
    vhost: str,
) -> tuple[list[dict[str, typing.Any]], list[dict[str, typing.Any]]]:
    """Exchanges and queues of the universe, with their bindings and pending messages, see `snapshot._read_mq`."""
    quoted_vhost = quote(vhost)
    exchanges = [
        {field: exchange[field] for field in EXCHANGE_FIELDS}
        for exchange in call("GET", f"exchanges/{quoted_vhost}")
        if is_agent_exchange(exchange["name"]) is True
    ]
    queues = []
    for queue in call("GET", f"queues/{quoted_vhost}"):
        name = quote(queue["name"])
        bindings = [
            {
                "source": binding["source"],
                "routing_key": binding["routing_key"],
                "arguments": binding["arguments"],
            }
            for binding in call("GET", f"queues/{quoted_vhost}/{name}/bindings")
            if is_agent_exchange(binding["source"]) is True
        ]
        messages = [
            {
                "routing_key": message["routing_key"],
                # The management API returns an empty list for a message without properties.
                "properties": message["properties"] or {},
                "payload": message["payload"],
                "payload_encoding": message["payload_encoding"],
            }
            for message in call(
                "POST",
                f"queues/{quoted_vhost}/{name}/get",
                {
                    "count": MAX_QUEUE_MESSAGES,
                    # The messages are put back in the queue once read.
                    "ackmode": "ack_requeue_true",
                    "encoding": "base64",
                },
            )
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


def capture_redis(connection: RedisConnection) -> list[dict[str, typing.Any]]:
    """Every key of the Redis of the universe, serialized by `DUMP`, see `snapshot._dump_redis`."""
    keys = []
    cursor = b"0"
    while True:
        cursor, batch = connection.command(b"SCAN", cursor, b"COUNT", REDIS_SCAN_COUNT)
        for key in batch:
            value = connection.command(b"DUMP", key)
            ttl_ms = connection.command(b"PTTL", key)
            if value is None or ttl_ms == -2:
                # The key expired between the scan and the dump.
                continue
            keys.append(
                {
                    "key": base64.b64encode(key).decode(),
                    "ttl_ms": max(ttl_ms, 0),
                    "value": base64.b64encode(value).decode(),
                }
            )
        if cursor == b"0":
            return keys


def is_agent_exchange(name: str) -> bool:
    """The default exchange and the `amq.*` exchanges exist in every broker, they are not captured."""
    return name != "" and name.startswith("amq.") is False


def quote(name: str) -> str:
    return parse.quote(name, safe="")


def main(args: list[str]) -> int:
    """Capture the state of the vhost given as the first argument and of the Redis host given as the second, and
    write it to the JSON file given as the third."""
    vhost, redis_host, output_path = args[1], args[2], args[3]
    exchanges, queues = capture_mq(vhost)
    connection = RedisConnection(redis_host)
    try:
        redis_keys = capture_redis(connection)
    finally:
        connection.close()
    with open(output_path, "w") as output_file:
        json.dump(
            {"exchanges": exchanges, "queues": queues, "redis_keys": redis_keys},
            output_file,
        )
    messages = sum(len(queue["messages"]) for queue in queues)
    print(
        f"captured {len(queues)} queues, {messages} messages and {len(redis_keys)} redis keys"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
