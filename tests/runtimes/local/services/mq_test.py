"""Test local RabbitMQ service.

Tests marked with `docker` require access to working docker instance (socket or host). Make sure to disable them
on instances missing docker.
"""

import docker
import pytest

from ostorlab.runtimes.local.services import mq


@pytest.mark.docker
def testLocalRabbitMQStart_onOperationalConditions_rabbitMQServiceIsStarted():
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
