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


def testLocalRabbitMQAttach_whenServiceIsRunning_usesItAndReturnsTrue(
    mocker: plugin.MockerFixture,
) -> None:
    """The MQ service started by the process running the scan is found by its name."""
    docker_client = mocker.MagicMock()
    mocker.patch("docker.from_env", return_value=docker_client)
    lrm = mq.LocalRabbitMQ(name="7", network="test_network")

    assert lrm.attach() is True
    docker_client.services.get.assert_called_once_with("mq_7")
    assert lrm.service is docker_client.services.get.return_value


def testLocalRabbitMQAttach_whenServiceIsMissing_returnsFalse(
    mocker: plugin.MockerFixture,
) -> None:
    """A universe without MQ service has nothing to capture."""
    docker_client = mocker.MagicMock()
    docker_client.services.get.side_effect = docker.errors.NotFound("no service")
    mocker.patch("docker.from_env", return_value=docker_client)
    lrm = mq.LocalRabbitMQ(name="7", network="test_network")

    assert lrm.attach() is False
    assert lrm.service is None


def testLocalRabbitMQCapture_always_runsCaptureScriptInsideMqContainerAndReadsItsState(
    mocker: plugin.MockerFixture,
) -> None:
    """The capture script is copied to the MQ container and run there, the state it writes is read back."""
    lrm, _ = _mock_mq_with_task(mocker, task_state="running", exit_code=0)
    run = mocker.patch.object(container_exec, "run", return_value=b"captured 1 queues")
    state: dict[str, list[str]] = {"exchanges": [], "queues": [], "redis_keys": []}
    read_file = mocker.patch.object(
        container_exec, "read_file", return_value=json.dumps(state).encode()
    )

    captured = lrm.capture(redis_host="redis_test_mq")

    assert captured == state
    _, service, command = run.call_args.args
    assert service is lrm.service
    assert command[:2] == ["sh", "-c"]
    assert command[2].startswith(
        f"python3 /tmp/{mq.SNAPSHOT_CAPTURE_SCRIPT_FILE} / redis_test_mq "
        f"/tmp/{mq.SNAPSHOT_CAPTURE_STATE_FILE}"
    )
    assert (
        run.call_args.kwargs["files"][mq.SNAPSHOT_CAPTURE_SCRIPT_FILE]
        == mq.SNAPSHOT_CAPTURE_SCRIPT.read_bytes()
    )
    assert read_file.call_args.args[1:] == (
        lrm.service,
        f"/tmp/{mq.SNAPSHOT_CAPTURE_STATE_FILE}",
    )


def testLocalRabbitMQCapture_whenStateIsNotJson_raisesExecError(
    mocker: plugin.MockerFixture,
) -> None:
    """A state that cannot be decoded is reported as a failed capture."""
    lrm, _ = _mock_mq_with_task(mocker, task_state="running", exit_code=0)
    mocker.patch.object(container_exec, "run", return_value=b"")
    mocker.patch.object(container_exec, "read_file", return_value=b"not json")

    with pytest.raises(container_exec.ExecError):
        lrm.capture(redis_host="redis_test_mq")
