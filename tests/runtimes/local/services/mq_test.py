"""Test local RabbitMQ service.

Tests marked with `docker` require access to working docker instance (socket or host). Make sure to disable them
on instances missing docker.
"""

import json
from unittest import mock

import docker
import pytest
from pytest_mock import plugin

from ostorlab.runtimes.local.services import container_exec
from ostorlab.runtimes.local.services import mq


@pytest.mark.docker
def testLocalRabbitMQStart_onOperationalConditions_rabbitMQServiceIsStarted() -> None:
    """Test service is healthy after start and unhealthy after stop."""
    lrm = mq.LocalRabbitMQ(name="test_mq", network="test_network")
    lrm.start()

    assert lrm.is_healthy is True
    lrm.stop()

    assert lrm.is_healthy is False


@pytest.mark.docker
def testLocalRabbitMQStart_always_rabbitMQServiceIsStartedWithFixedHostname(
    mq_service: mq.LocalRabbitMQ,
) -> None:
    """Test MQ service is started with a fixed host name."""
    d_client = docker.from_env()

    service = d_client.services.list(filters={"name": "mq_core_mq"})[0]

    assert service.attrs["Spec"]["TaskTemplate"]["ContainerSpec"]["Hostname"] == "mq"
    assert service.attrs["Spec"]["TaskTemplate"]["ContainerSpec"]["Mounts"] == [
        {"Source": "core_mq_mq_data", "Target": "/var/lib/rabbitmq", "Type": "volume"}
    ]


def _mock_mq_with_task(
    mocker: plugin.MockerFixture, task_state: str, exit_code: int
) -> tuple[mq.LocalRabbitMQ, mock.MagicMock]:
    docker_client = mocker.MagicMock()
    docker_client.containers.get.return_value.exec_run.return_value = mocker.Mock(
        exit_code=exit_code
    )
    mocker.patch("docker.from_env", return_value=docker_client)
    lrm = mq.LocalRabbitMQ(name="test_mq", network="test_network")
    service = mocker.MagicMock()
    service.tasks.return_value = [
        {"Status": {"State": task_state, "ContainerStatus": {"ContainerID": "abc123"}}}
    ]
    lrm._mq_service = service
    return lrm, docker_client


def testLocalRabbitMQIsAcceptingConnections_whenReadinessCheckSucceeds_returnsTrue(
    mocker: plugin.MockerFixture,
) -> None:
    """The readiness check runs inside the MQ container and its success means RabbitMQ accepts connections."""
    lrm, docker_client = _mock_mq_with_task(mocker, task_state="running", exit_code=0)

    assert lrm.is_accepting_connections is True
    docker_client.containers.get.assert_called_once_with("abc123")
    docker_client.containers.get.return_value.exec_run.assert_called_once_with(
        mq.MQ_READINESS_COMMAND
    )


def testLocalRabbitMQIsAcceptingConnections_whenReadinessCheckFails_returnsFalse(
    mocker: plugin.MockerFixture,
) -> None:
    """A running container whose RabbitMQ listeners are not up yet is not ready."""
    lrm, _ = _mock_mq_with_task(mocker, task_state="running", exit_code=69)

    assert lrm.is_accepting_connections is False


def testLocalRabbitMQIsAcceptingConnections_whenNoRunningTask_returnsFalse(
    mocker: plugin.MockerFixture,
) -> None:
    """Without a running task there is no container to check."""
    lrm, docker_client = _mock_mq_with_task(mocker, task_state="starting", exit_code=0)

    assert lrm.is_accepting_connections is False
    docker_client.containers.get.assert_not_called()


def testLocalRabbitMQRestore_always_runsRestoreScriptInsideMqContainer(
    mocker: plugin.MockerFixture,
) -> None:
    """The state and the restore script are copied to the MQ container and run there in one exec."""
    lrm, _ = _mock_mq_with_task(mocker, task_state="running", exit_code=0)
    run = mocker.patch.object(
        container_exec, "run", return_value=b"restored 1 queues and 2 messages"
    )
    queues = [{"name": "nmap", "bindings": [], "messages": []}]

    lrm.restore(exchanges=[], queues=queues)

    _, service, command = run.call_args.args
    files = run.call_args.kwargs["files"]
    assert service is lrm.service
    assert command[:2] == ["sh", "-c"]
    assert command[2].startswith(
        f"python3 /tmp/{mq.MQ_RESTORE_SCRIPT_FILE} /tmp/{mq.MQ_RESTORE_STATE_FILE}"
    )
    assert files[mq.MQ_RESTORE_SCRIPT_FILE] == mq.MQ_RESTORE_SCRIPT.read_bytes()
    assert json.loads(files[mq.MQ_RESTORE_STATE_FILE]) == {
        "vhost": "/",
        "exchanges": [],
        "queues": queues,
    }


def testLocalRabbitMQRestore_whenStateIsEmpty_doesNotRunRestoreScript(
    mocker: plugin.MockerFixture,
) -> None:
    """Nothing to restore, the script is not copied nor run."""
    lrm, _ = _mock_mq_with_task(mocker, task_state="running", exit_code=0)
    run = mocker.patch.object(container_exec, "run")

    lrm.restore(exchanges=[], queues=[])

    run.assert_not_called()


def testLocalRabbitMQRestore_whenScriptFails_raisesExecError(
    mocker: plugin.MockerFixture,
) -> None:
    """A failing restore is reported to the runtime."""
    lrm, _ = _mock_mq_with_task(mocker, task_state="running", exit_code=1)
    queues = [{"name": "nmap", "bindings": [], "messages": []}]

    with pytest.raises(container_exec.ExecError):
        lrm.restore(exchanges=[], queues=queues)
