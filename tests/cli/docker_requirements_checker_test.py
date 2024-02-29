"""Tests for the docker_requirements_checker module."""

import pytest
from pytest_mock import plugin

from ostorlab import exceptions
from ostorlab.cli import docker_requirements_checker


@pytest.mark.docker
def testRuntime_WhenCantInitSwarm_shouldRetry(
    mocker: plugin.MockerFixture, httpx_mock
) -> None:
    """Ensure the runtime retries to init swarm if it fails the first time."""
    mocker.patch("time.sleep")
    httpx_mock.add_response(
        url="http+docker://localhost/version", json={"ApiVersion": "1.35"}
    )
    httpx_mock.add_response(
        url="http+docker://localhost/v1.35/swarm", json={"ID": "1234"}
    )
    httpx_mock.add_response(
        url="http+docker://localhost/v1.35/swarm/init", status_code=400
    )

    with pytest.raises(exceptions.OstorlabError):
        docker_requirements_checker.init_swarm()

    assert len(httpx_mock.get_requests()) == 3
