"""Unit tests for running commands in the container of a service."""

import io
import tarfile
from unittest import mock

import pytest
from docker import errors
from pytest_mock import plugin

from ostorlab.runtimes.local.services import container_exec


def _mock_service(
    mocker: plugin.MockerFixture, task_state: str = "running"
) -> mock.MagicMock:
    service: mock.MagicMock = mocker.MagicMock()
    service.name = "redis_1"
    service.tasks.return_value = [
        {"Status": {"State": task_state, "ContainerStatus": {"ContainerID": "abc123"}}}
    ]
    return service


def testRun_whenCommandSucceeds_copiesFilesAndReturnsOutput(
    mocker: plugin.MockerFixture,
) -> None:
    """Files are copied to the running container before the command runs in it."""
    docker_client = mocker.MagicMock()
    container = docker_client.containers.get.return_value
    container.exec_run.return_value = mocker.Mock(exit_code=0, output=b"done")

    output = container_exec.run(
        docker_client,
        _mock_service(mocker),
        ["cat", "/tmp/data"],
        files={"data": b"\x00content"},
    )

    assert output == b"done"
    docker_client.containers.get.assert_called_once_with("abc123")
    container.exec_run.assert_called_once_with(["cat", "/tmp/data"])
    directory, archive = container.put_archive.call_args.args
    assert directory == container_exec.FILES_DIRECTORY
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        member = tar.extractfile("data")
        assert member is not None
        assert member.read() == b"\x00content"


def testRun_whenCommandFails_raisesExecErrorWithOutput(
    mocker: plugin.MockerFixture,
) -> None:
    """A failing command reports its output."""
    docker_client = mocker.MagicMock()
    docker_client.containers.get.return_value.exec_run.return_value = mocker.Mock(
        exit_code=1, output=b"errors: 1"
    )

    with pytest.raises(container_exec.ExecError, match="errors: 1"):
        container_exec.run(docker_client, _mock_service(mocker), ["redis-cli"])


def testRun_whenNoRunningContainer_raisesExecError(
    mocker: plugin.MockerFixture,
) -> None:
    """Without a running task there is no container to run the command in."""
    docker_client = mocker.MagicMock()

    with pytest.raises(container_exec.ExecError):
        container_exec.run(
            docker_client, _mock_service(mocker, task_state="starting"), ["redis-cli"]
        )

    docker_client.containers.get.assert_not_called()


def testRun_whenServiceIsNotStarted_raisesExecError(
    mocker: plugin.MockerFixture,
) -> None:
    """A service that failed to start has no container."""
    with pytest.raises(container_exec.ExecError):
        container_exec.run(mocker.MagicMock(), None, ["redis-cli"])


def testRun_whenDockerFails_raisesExecError(mocker: plugin.MockerFixture) -> None:
    """Docker errors are reported as exec errors."""
    docker_client = mocker.MagicMock()
    docker_client.containers.get.side_effect = errors.NotFound("gone")

    with pytest.raises(container_exec.ExecError):
        container_exec.run(docker_client, _mock_service(mocker), ["redis-cli"])
