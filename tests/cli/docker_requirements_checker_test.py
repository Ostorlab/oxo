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


def testInitSwarm_whenInterfaceHasMultipleAddresses_shouldAdvertiseLoopbackAddress(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure swarm init falls back to the loopback address when Docker can't choose one."""
    mock_docker = mocker.MagicMock()
    mock_docker.swarm.init.side_effect = [
        errors.APIError(
            "could not choose an IP address to advertise since this system has multiple addresses on "
            "interface wlp1s0 - specify one with --advertise-addr"
        ),
        None,
    ]
    mocker.patch("docker.from_env", return_value=mock_docker)

    docker_requirements_checker.init_swarm()

    assert mock_docker.swarm.init.call_count == 2
    assert mock_docker.swarm.init.call_args_list[1].kwargs == {
        "advertise_addr": "127.0.0.1"
    }


def testInitSwarm_whenApiErrorIsUnrelated_shouldNotAdvertiseLoopbackAddress(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure other swarm init errors keep the existing retry behaviour."""
    mocker.patch("time.sleep")
    mock_docker = mocker.MagicMock()
    mock_docker.swarm.init.side_effect = errors.APIError("some other error")
    mocker.patch("docker.from_env", return_value=mock_docker)

    with pytest.raises(exceptions.OstorlabError):
        docker_requirements_checker.init_swarm()

    assert all(call.kwargs == {} for call in mock_docker.swarm.init.call_args_list)
