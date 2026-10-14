"""Restore the RabbitMQ state of a paused universe, run with python3 inside the MQ container before the agents start.

`LocalRabbitMQ.restore` copies this script and the state to restore to the container, then runs it. It only uses the
standard library of the python3 shipped with the RabbitMQ management image, and talks to the management API on
localhost.

Messages are published to a temporary fanout exchange bound to their queue only: each message lands in the queue it
was taken from with its original routing key, which agents read as the message selector, and its properties unchanged.
"""

from __future__ import annotations

import base64
import json
import sys
import time
import typing
from urllib import parse
from urllib import request

MANAGEMENT_API_URL = "http://localhost:15672/api"
CREDENTIALS = base64.b64encode(b"guest:guest").decode()
REQUEST_TIMEOUT_SECONDS = 60
READINESS_ATTEMPTS = 60
READINESS_WAIT_SECONDS = 1
# Prefix of the temporary exchanges, one per queue, followed by the index of the queue in the state.
RESTORE_EXCHANGE_PREFIX = "ostorlab.snapshot.restore."


class Error(Exception):
    """Base error of the MQ restore script."""


class RestoreError(Error):
    """A message could not be put back in its queue."""


def call(method: str, path: str, body: typing.Any = None) -> typing.Any:
    """Call the management API and return the decoded JSON response, None when it has no body."""
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
        content = response.read()
    return json.loads(content) if len(content) > 0 else None


def wait_ready() -> None:
    """Wait for the management API, it starts after the AMQP listener the readiness check waits for."""
    for attempt in range(READINESS_ATTEMPTS):
        try:
            call("GET", "overview")
            return
        except OSError:
            if attempt == READINESS_ATTEMPTS - 1:
                raise
            time.sleep(READINESS_WAIT_SECONDS)


def restore(state: dict[str, typing.Any]) -> int:
    """Declare the exchanges, the queues and their bindings, then put back the messages in their queues.

    Returns:
        The number of restored messages.
    """
    vhost = quote(state["vhost"])
    for exchange in state["exchanges"]:
        call(
            "PUT",
            f"exchanges/{vhost}/{quote(exchange['name'])}",
            {key: value for key, value in exchange.items() if key != "name"},
        )
    return sum(
        restore_queue(vhost, index, queue)
        for index, queue in enumerate(state["queues"])
    )


def restore_queue(vhost: str, index: int, queue: dict[str, typing.Any]) -> int:
    name = quote(queue["name"])
    call(
        "PUT",
        f"queues/{vhost}/{name}",
        {
            "durable": queue["durable"],
            "auto_delete": queue["auto_delete"],
            "arguments": queue["arguments"],
        },
    )
    for binding in queue["bindings"]:
        call(
            "POST",
            f"bindings/{vhost}/e/{quote(binding['source'])}/q/{name}",
            {"routing_key": binding["routing_key"], "arguments": binding["arguments"]},
        )
    if len(queue["messages"]) == 0:
        return 0
    restore_exchange = quote(f"{RESTORE_EXCHANGE_PREFIX}{index}")
    call(
        "PUT",
        f"exchanges/{vhost}/{restore_exchange}",
        {"type": "fanout", "durable": False},
    )
    try:
        call(
            "POST",
            f"bindings/{vhost}/e/{restore_exchange}/q/{name}",
            {"routing_key": "", "arguments": {}},
        )
        for message in queue["messages"]:
            result = call(
                "POST",
                f"exchanges/{vhost}/{restore_exchange}/publish",
                {
                    "properties": message["properties"],
                    "routing_key": message["routing_key"],
                    "payload": message["payload"],
                    "payload_encoding": message["payload_encoding"],
                },
            )
            if result.get("routed") is not True:
                raise RestoreError(f"message not routed to queue {queue['name']}.")
    finally:
        # Deleting the exchange removes its binding to the queue.
        call("DELETE", f"exchanges/{vhost}/{restore_exchange}")
    return len(queue["messages"])


def quote(name: str) -> str:
    return parse.quote(name, safe="")


def main(args: list[str]) -> int:
    """Restore the state stored in the JSON file given as the first argument."""
    with open(args[1], "rb") as state_file:
        state = json.load(state_file)
    wait_ready()
    messages = restore(state)
    print(f"restored {len(state['queues'])} queues and {messages} messages")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
