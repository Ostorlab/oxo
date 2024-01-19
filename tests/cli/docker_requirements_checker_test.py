import pytest
from pytest_mock import plugin
from requests_mock import mocker as req_mocker

from ostorlab import exceptions
from ostorlab.cli import docker_requirements_checker


@pytest.mark.docker
def testRuntime_WhenCantInitSwarm_shouldRetry(
    mocker: plugin.MockerFixture, requests_mock: req_mocker.Mocker
):
    """Ensure the runtime retries to init swarm if it fails the first time."""
    mocker.patch("time.sleep")
    requests_mock.get(
        "http+docker://localhost/version", [{"json": {"ApiVersion": "1.35"}}]
    )
    requests_mock.get("http+docker://localhost/v1.35/swarm", json={"ID": "1234"})
    mock_swarm_init = requests_mock.post(
        "http+docker://localhost/v1.35/swarm/init", status_code=400
    )

    with pytest.raises(exceptions.OstorlabError):
        docker_requirements_checker.init_swarm()

    assert mock_swarm_init.call_count == 3
