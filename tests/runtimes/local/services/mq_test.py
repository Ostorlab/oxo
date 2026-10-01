"""Test local RabbitMQ service.

Tests marked with `docker` require access to working docker instance (socket or host). Make sure to disable them
on instances missing docker.
"""

import docker
import pytest
import tenacity
from docker.models import services
from pytest_mock import plugin

from ostorlab.runtimes.local.services import jaeger
from ostorlab.runtimes.local.services import mq
from ostorlab.runtimes.local.services import redis


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


def _mock_mq_with_task(
    mocker: plugin.MockerFixture, task_state: str, exit_code: int
) -> tuple[mq.LocalRabbitMQ, object]:
    docker_client = mocker.MagicMock()
    docker_client.containers.get.return_value.exec_run.return_value = mocker.Mock(
        exit_code=exit_code
    )
    mocker.patch("docker.from_env", return_value=docker_client)
    lrm = mq.LocalRabbitMQ(name="test_mq", network="test_network")
    service = mocker.MagicMock()
    service.tasks.return_value = [
        {"Status": {"State": task_state, "ContainerStatus": {"ContainerID": "abc123"}}}
    ]
    lrm._mq_service = service
    return lrm, docker_client


def testLocalRabbitMQIsAcceptingConnections_whenReadinessCheckSucceeds_returnsTrue(
    mocker: plugin.MockerFixture,
) -> None:
    """The readiness check runs inside the MQ container and its success means RabbitMQ accepts connections."""
    lrm, docker_client = _mock_mq_with_task(mocker, task_state="running", exit_code=0)

    assert lrm.is_accepting_connections is True
    docker_client.containers.get.assert_called_once_with("abc123")
    docker_client.containers.get.return_value.exec_run.assert_called_once_with(
        mq.MQ_READINESS_COMMAND
    )


def testLocalRabbitMQIsAcceptingConnections_whenReadinessCheckFails_returnsFalse(
    mocker: plugin.MockerFixture,
) -> None:
    """A running container whose RabbitMQ listeners are not up yet is not ready."""
    lrm, _ = _mock_mq_with_task(mocker, task_state="running", exit_code=69)

    assert lrm.is_accepting_connections is False


def testLocalRabbitMQIsAcceptingConnections_whenNoRunningTask_returnsFalse(
    mocker: plugin.MockerFixture,
) -> None:
    """Without a running task there is no container to check."""
    lrm, docker_client = _mock_mq_with_task(mocker, task_state="starting", exit_code=0)

    assert lrm.is_accepting_connections is False
    docker_client.containers.get.assert_not_called()


def testLocalRabbitMQServiceReadiness_whenListenersNeverReady_returnsFalse(
    mocker: plugin.MockerFixture,
) -> None:
    """A running task cannot bypass exhausted RabbitMQ listener readiness checks."""
    lrm, docker_client = _mock_mq_with_task(mocker, task_state="running", exit_code=69)
    check_health = mq.LocalRabbitMQ.is_service_healthy.retry_with(
        stop=tenacity.stop_after_attempt(2), wait=tenacity.wait_none()
    )

    assert check_health(lrm) is False
    assert docker_client.containers.get.return_value.exec_run.call_count == 2


@pytest.mark.parametrize(
    ("helper_class", "service_prefix"),
    [
        (mq.LocalRabbitMQ, "mq_"),
        (redis.LocalRedis, "redis_"),
        (jaeger.LocalJaeger, "jaeger_"),
    ],
)
def testLocalServiceStop_whenUniversesShareDigits_removesOnlyOwnedHelper(
    mocker: plugin.MockerFixture,
    offline_docker_client: docker.DockerClient,
    helper_class: type[mq.LocalRabbitMQ | redis.LocalRedis | jaeger.LocalJaeger],
    service_prefix: str,
) -> None:
    """Stopping one universe preserves neighboring and unrelated services."""
    service_definitions = [
        (f"{service_prefix}1", {"ostorlab.universe": "1"}),
        (f"{service_prefix}11", {"ostorlab.universe": "11"}),
        (f"{service_prefix}21", {"ostorlab.universe": "21"}),
        (f"{service_prefix}unlabeled", {}),
        ("unrelated_1", {"ostorlab.universe": "1"}),
    ]
    docker_services = [
        services.Service(
            attrs={
                "ID": service_name,
                "Spec": {"Name": service_name, "Labels": labels},
            },
            client=offline_docker_client,
        )
        for service_name, labels in service_definitions
    ]
    list_services = mocker.patch.object(
        services.ServiceCollection,
        "list",
        autospec=True,
        return_value=docker_services,
    )
    remove_service = mocker.patch.object(
        offline_docker_client.api, "remove_service", autospec=True
    )
    helper = helper_class(name="1", network="test_network")

    helper.stop()

    remove_service.assert_called_once_with(f"{service_prefix}1")
    list_services.assert_called_once_with(
        mocker.ANY, filters={"label": "ostorlab.universe=1"}
    )
