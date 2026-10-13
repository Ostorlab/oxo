"""Unit tests for the script restoring the RabbitMQ state inside the MQ container."""

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


def testRestore_always_declaresTopologyAndRoutesMessagesToTheirQueue(
    mocker: plugin.MockerFixture,
) -> None:
    """Each message is published through the restore exchange to its own queue with its routing key."""
    call = mocker.patch.object(mq_restore_script, "call", return_value={"routed": True})

    restored = mq_restore_script.restore(STATE)

    assert restored == 1
    calls = [(c.args[0], c.args[1]) for c in call.call_args_list]
    assert calls == [
        ("PUT", "exchanges/%2F/ostorlab_topic_1"),
        ("PUT", "exchanges/%2F/ostorlab.snapshot.restore"),
        ("PUT", "queues/%2F/nmap"),
        ("POST", "bindings/%2F/e/ostorlab_topic_1/q/nmap"),
        ("POST", "bindings/%2F/e/ostorlab.snapshot.restore/q/nmap"),
        ("POST", "exchanges/%2F/ostorlab.snapshot.restore/publish"),
        ("DELETE", "exchanges/%2F/ostorlab.snapshot.restore"),
    ]
    publish_body = call.call_args_list[5].args[2]
    assert publish_body["routing_key"] == "v3.asset.ip.v4"
    assert publish_body["payload"] == "AG1lc3NhZ2U="
    assert publish_body["properties"] == {
        "priority": 1,
        "headers": {"trace": "1", mq_restore_script.RESTORE_QUEUE_HEADER: "nmap"},
    }
    assert call.call_args_list[2].args[2] == {
        "durable": True,
        "auto_delete": False,
        "arguments": {"x-max-priority": 3},
    }


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
        "exchanges/%2F/ostorlab.snapshot.restore",
    )


def testMain_always_waitsForManagementApiThenRestoresStateFile(
    mocker: plugin.MockerFixture, tmp_path: pathlib.Path
) -> None:
    """The script restores the state file passed as argument."""
    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps(STATE))
    wait_ready = mocker.patch.object(mq_restore_script, "wait_ready")
    restore = mocker.patch.object(mq_restore_script, "restore", return_value=1)

    assert mq_restore_script.main(["script", str(state_file)]) == 0
    wait_ready.assert_called_once()
    restore.assert_called_once_with(STATE)


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
