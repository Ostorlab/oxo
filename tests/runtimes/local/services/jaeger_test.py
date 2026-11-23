"""Test local Jaeger service.

Tests marked with `docker` require access to working docker instance (socket or host). Make sure to disable them
on instances missing docker.
"""

import pytest
from pytest_mock import plugin

from ostorlab.runtimes.local.services import jaeger


@pytest.mark.docker
def testLocalJaeger_onOperationalConditions_jaegerIsStarted() -> None:
    """Test service is healthy after start and unhealthy after stop."""
    lj = jaeger.LocalJaeger(name="test_redis", network="test_network")
    lj.start()

    assert lj.is_healthy is True
    lj.stop()

    assert lj.is_healthy is False


def testLocalJaegerIsServiceHealthy_whenServiceIsMissing_returnsFalse(
    mocker: plugin.MockerFixture,
) -> None:
    """A missing Docker service is unhealthy without accessing its name."""
    mocker.patch("docker.from_env")
    mocker.patch("time.sleep")
    service = jaeger.LocalJaeger(name="missing", network="test_network")

    assert service.service is None
    assert service.is_service_healthy() is False
