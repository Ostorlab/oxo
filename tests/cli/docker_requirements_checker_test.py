"""Tests for the docker_requirements_checker module."""

import pytest
from docker import errors
from pytest_mock import plugin

from ostorlab import exceptions
from ostorlab.cli import docker_requirements_checker


@pytest.mark.docker
def testRuntime_WhenCantInitSwarm_shouldRetry(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure the runtime retries to init swarm if it fails the first time."""
    mocker.patch("time.sleep")
    mock_docker = mocker.MagicMock()
    mock_docker.swarm.init.side_effect = errors.DockerException("error")
    mocker.patch("docker.from_env", return_value=mock_docker)

    with pytest.raises(exceptions.OstorlabError):
        docker_requirements_checker.init_swarm()

    assert mock_docker.swarm.init.call_count == 10
