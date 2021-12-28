"""Test local RabbitMQ service.

Tests marked with `docker` require access to working docker instance (socket or host). Make sure to disable them
on instances missing docker.
"""

import pytest

from ostorlab.runtimes.local.services import mq


@pytest.mark.docker
def testLocalRabbitMQStart_onOperationalConditions_rabbitMQServiceIsStarted():
    """Test service is healthy after start and unhealthy after stop."""
    lrm = mq.LocalRabbitMQ(name='test_mq', network='test_network')
    lrm.start()

    assert lrm.is_healthy is True
    lrm.stop()

    assert lrm.is_healthy is False
