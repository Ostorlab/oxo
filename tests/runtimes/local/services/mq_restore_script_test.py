"""Unit tests for the script restoring the RabbitMQ state inside the MQ container."""

import copy
import json
import pathlib
import typing

import pytest
from pytest_mock import plugin

from ostorlab.runtimes.local.services import mq_restore_script

STATE: dict[str, typing.Any] = {
    "vhost": "/",
    "exchanges": [
        {
            "name": "ostorlab_topic_1",
            "type": "topic",
            "durable": False,
            "auto_delete": False,
            "internal": False,
            "arguments": {},
        }
    ],
    "queues": [
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
                    "properties": {"priority": 1, "headers": {"trace": "1"}},
                    "payload": "AG1lc3NhZ2U=",
                    "payload_encoding": "base64",
                }
            ],
        }
    ],
}


@pytest.fixture(autouse=True)
def restore_exchange_suffix(mocker: plugin.MockerFixture) -> None:
    """A fixed suffix for the temporary restore exchanges."""
    mocker.patch("uuid.uuid4", return_value=mocker.Mock(hex="run"))


def testRestore_always_declaresTopologyAndRoutesMessagesToTheirQueue(
    mocker: plugin.MockerFixture,
) -> None:
    """Each message is published through a fanout exchange bound to its queue only, with its routing key."""
    call = mocker.patch.object(mq_restore_script, "call", return_value={"routed": True})

    restored = mq_restore_script.restore(STATE)

    assert restored == 1
    calls = [(c.args[0], c.args[1]) for c in call.call_args_list]
    assert calls == [
        ("PUT", "exchanges/%2F/ostorlab_topic_1"),
        ("PUT", "queues/%2F/nmap"),
        ("POST", "bindings/%2F/e/ostorlab_topic_1/q/nmap"),
        ("PUT", "exchanges/%2F/ostorlab.snapshot.restore.run"),
        ("POST", "bindings/%2F/e/ostorlab.snapshot.restore.run/q/nmap"),
        ("POST", "exchanges/%2F/ostorlab.snapshot.restore.run/publish"),
        ("DELETE", "exchanges/%2F/ostorlab.snapshot.restore.run"),
    ]
    assert call.call_args_list[3].args[2] == {"type": "fanout", "durable": False}
    assert call.call_args_list[1].args[2] == {
        "durable": True,
        "auto_delete": False,
        "arguments": {"x-max-priority": 3},
    }


def testRestore_always_keepsMessageRoutingKeyAndPropertiesUnchanged(
    mocker: plugin.MockerFixture,
) -> None:
    """The restored message is the one taken from the queue, no restore header is added."""
    call = mocker.patch.object(mq_restore_script, "call", return_value={"routed": True})

    mq_restore_script.restore(STATE)

    publish_body = call.call_args_list[5].args[2]
    assert publish_body == {
        "properties": {"priority": 1, "headers": {"trace": "1"}},
        "routing_key": "v3.asset.ip.v4",
        "payload": "AG1lc3NhZ2U=",
        "payload_encoding": "base64",
    }


def testRestore_whenQueueHasNoMessages_doesNotDeclareRestoreExchange(
    mocker: plugin.MockerFixture,
) -> None:
    """An empty queue only gets its declaration and bindings back."""
    call = mocker.patch.object(mq_restore_script, "call", return_value={"routed": True})
    state = copy.deepcopy(STATE)
    state["queues"][0]["messages"] = []

    restored = mq_restore_script.restore(state)

    assert restored == 0
    assert all(
        "ostorlab.snapshot.restore" not in c.args[1] for c in call.call_args_list
    )


def testRestore_whenMessageIsNotRouted_raisesAndDeletesRestoreExchange(
    mocker: plugin.MockerFixture,
) -> None:
    """A message that reaches no queue fails the restore, the restore exchange is still removed."""
    call = mocker.patch.object(
        mq_restore_script, "call", return_value={"routed": False}
    )

    with pytest.raises(mq_restore_script.RestoreError):
        mq_restore_script.restore(STATE)

    assert call.call_args_list[-1].args[:2] == (
        "DELETE",
        "exchanges/%2F/ostorlab.snapshot.restore.run",
    )


def testRestore_whenCleanupFailsAfterRestoreError_raisesRestoreError(
    mocker: plugin.MockerFixture,
) -> None:
    """A failed delete of the restore exchange does not hide why the restore failed."""

    def call(method: str, path: str, body: typing.Any = None) -> typing.Any:
        if method == "DELETE":
            raise ConnectionResetError("closed")
        return {"routed": False}

    mocker.patch.object(mq_restore_script, "call", side_effect=call)

    with pytest.raises(mq_restore_script.RestoreError):
        mq_restore_script.restore(STATE)


def testRestoreQueue_always_usesANewRestoreExchangeName(
    mocker: plugin.MockerFixture,
) -> None:
    """Each restore declares its own exchange, never one captured or left by a previous restore."""
    mocker.patch(
        "uuid.uuid4",
        side_effect=[mocker.Mock(hex="first"), mocker.Mock(hex="second")],
    )
    call = mocker.patch.object(mq_restore_script, "call", return_value={"routed": True})

    mq_restore_script.restore(STATE)
    mq_restore_script.restore(STATE)

    declared = [
        c.args[1]
        for c in call.call_args_list
        if c.args[0] == "PUT" and "ostorlab.snapshot.restore" in c.args[1]
    ]
    assert declared == [
        "exchanges/%2F/ostorlab.snapshot.restore.first",
        "exchanges/%2F/ostorlab.snapshot.restore.second",
    ]


def testMain_always_restoresStateFileAndReportsRestoredMessages(
    mocker: plugin.MockerFixture,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The script restores the state file passed as argument, only the management API transport is mocked."""
    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps(STATE))
    call = mocker.patch.object(mq_restore_script, "call", return_value={"routed": True})

    status = mq_restore_script.main(["script", str(state_file)])

    assert status == 0
    assert capsys.readouterr().out == "restored 1 queues and 1 messages\n"
    assert call.call_args_list[0].args[:2] == ("GET", "overview")
    assert ("POST", "exchanges/%2F/ostorlab.snapshot.restore.run/publish") in [
        (c.args[0], c.args[1]) for c in call.call_args_list
    ]


def testWaitReady_whenManagementApiStartsLate_retries(
    mocker: plugin.MockerFixture,
) -> None:
    """The management API may not answer right after the AMQP listener."""
    mocker.patch("time.sleep")
    call = mocker.patch.object(
        mq_restore_script, "call", side_effect=[ConnectionRefusedError(), {}]
    )

    mq_restore_script.wait_ready()

    assert call.call_count == 2


def testCall_always_sendsAuthenticatedJsonRequest(
    mocker: plugin.MockerFixture,
) -> None:
    """The management API is called on localhost with the default credentials."""
    urlopen = mocker.patch("urllib.request.urlopen")
    urlopen.return_value.__enter__.return_value.read.return_value = b'{"routed": true}'

    response = mq_restore_script.call("POST", "exchanges/%2F/x/publish", {"a": 1})

    assert response == {"routed": True}
    api_request = urlopen.call_args.args[0]
    assert api_request.full_url == "http://localhost:15672/api/exchanges/%2F/x/publish"
    assert api_request.get_method() == "POST"
    assert api_request.data == b'{"a": 1}'
    assert api_request.get_header("Authorization") == "Basic Z3Vlc3Q6Z3Vlc3Q="
