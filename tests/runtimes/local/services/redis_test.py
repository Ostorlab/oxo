"""Test local Redis service.

Tests marked with `docker` require access to working docker instance (socket or host). Make sure to disable them
on instances missing docker.
"""

import pytest

from ostorlab.runtimes.local.services import redis


@pytest.mark.docker
def testLocalRedis_onOperationalConditions_redisIsStarted():
    """Test service is healthy after start and unhealthy after stop."""
    lr = redis.LocalRedis(name="test_redis", network="test_network")
    lr.start()

    assert lr.is_healthy is True
    lr.stop()

    assert lr.is_healthy is False
