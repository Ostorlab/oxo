"""Test local Jaeger service.

Tests marked with `docker` require access to working docker instance (socket or host). Make sure to disable them
on instances missing docker.
"""

import pytest

from ostorlab.runtimes.local.services import jaeger


@pytest.mark.docker
def testLocalJaeger_onOperationalConditions_jaegerIsStarted():
    """Test service is healthy after start and unhealthy after stop."""
    lj = jaeger.LocalJaeger(name="test_redis", network="test_network")
    lj.start()

    assert lj.is_healthy is True
    lj.stop()

    assert lj.is_healthy is False
