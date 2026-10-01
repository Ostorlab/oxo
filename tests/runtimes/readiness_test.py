"""Readiness retries must return booleans and prevent unhealthy scans."""

import unittest.mock

import docker
import pytest
import tenacity
from pytest_mock import plugin

from ostorlab.assets import ipv4
from ostorlab.cli import docker_requirements_checker
from ostorlab.runtimes import definitions
from ostorlab.runtimes.lite_local import runtime as lite_runtime
from ostorlab.runtimes.local import runtime as local_runtime
from ostorlab.runtimes.local.models import models
from ostorlab.runtimes.local.services import jaeger
from ostorlab.runtimes.local.services import mq
from ostorlab.runtimes.local.services import redis

_CoreService = mq.LocalRabbitMQ | redis.LocalRedis | jaeger.LocalJaeger
_Runtime = local_runtime.LocalRuntime | lite_runtime.LiteLocalRuntime


@pytest.fixture(params=[local_runtime.LocalRuntime, lite_runtime.LiteLocalRuntime])
def runtime_instance(
    request: pytest.FixtureRequest, mocker: plugin.MockerFixture
) -> _Runtime:
    """Use real readiness budgets without delays or a Docker daemon."""
    for name in [
        "is_docker_installed",
        "is_sys_arch_supported",
        "is_user_permitted",
        "is_docker_working",
        "is_swarm_initialized",
    ]:
        mocker.patch.object(docker_requirements_checker, name, return_value=True)
    mocker.patch("docker.from_env", return_value=mocker.MagicMock())
    runtime_type = request.param
    mocker.patch("time.sleep")
    mocker.patch.object(
        runtime_type,
        "_is_service_healthy",
        runtime_type._is_service_healthy.retry_with(wait=tenacity.wait_none()),
    )
    if runtime_type is local_runtime.LocalRuntime:
        return runtime_type(scan_id="1", run_default_agents=False)
    return runtime_type(
        scan_id="1",
        bus_url="bus",
        bus_vhost="/",
        bus_management_url="mgmt",
        bus_exchange_topic="topic",
        network="privnet",
        redis_url="redis://redis",
        tracing_collector_url="http://localhost:14268",
    )


@pytest.fixture(params=[mq.LocalRabbitMQ, redis.LocalRedis, jaeger.LocalJaeger])
def core_service(
    request: pytest.FixtureRequest, mocker: plugin.MockerFixture
) -> _CoreService:
    """Use real service checks without a Docker daemon or retry delays."""
    mocker.patch("docker.from_env", return_value=mocker.MagicMock())
    service_type = request.param
    mocker.patch.object(
        service_type,
        "is_service_healthy",
        service_type.is_service_healthy.retry_with(
            stop=tenacity.stop_after_attempt(2), wait=tenacity.wait_none()
        ),
    )
    return service_type(name="test", network="network")


def _set_service_tasks(
    service: _CoreService,
    mocker: plugin.MockerFixture,
    tasks: list[dict[str, object]],
) -> unittest.mock.MagicMock:
    docker_service = mocker.MagicMock()
    docker_service.tasks.return_value = tasks
    if isinstance(service, mq.LocalRabbitMQ):
        service._mq_service = docker_service
        service._docker_client.containers.get.return_value.exec_run.return_value = (
            mocker.Mock(exit_code=0)
        )
    elif isinstance(service, redis.LocalRedis):
        service._redis_service = docker_service
    else:
        service._jaeger_service = docker_service
    return docker_service


def _agent_service(mocker: plugin.MockerFixture) -> unittest.mock.MagicMock:
    service = mocker.MagicMock()
    service.name = "agent_test"
    service.attrs = {
        "Spec": {
            "Labels": {"ostorlab.universe": "1"},
            "Mode": {"Replicated": {"Replicas": 1}},
            "TaskTemplate": {"RestartPolicy": {"Condition": "any"}},
        }
    }
    service.tasks.return_value = []
    return service


def _mock_cleanup_resources(
    client: unittest.mock.MagicMock, service: unittest.mock.MagicMock
) -> None:
    client.services.list.return_value = [service]
    for collection in [client.networks, client.configs, client.volumes]:
        collection.list.return_value = []
    client.volumes.get.side_effect = docker.errors.NotFound("no volumes")


def testServiceReadiness_whenUnstarted_returnsFalse(
    core_service: _CoreService,
) -> None:
    """An unstarted service is unhealthy without dereferencing a missing service."""
    assert core_service.is_service_healthy() is False


def testServiceReadiness_whenRetriesExhausted_returnsFalse(
    core_service: _CoreService, mocker: plugin.MockerFixture
) -> None:
    """Exhausting unhealthy task checks returns an actual False value."""
    docker_service = _set_service_tasks(core_service, mocker, [])

    assert core_service.is_service_healthy() is False
    assert docker_service.tasks.call_count == 2


def testServiceReadiness_whenEventuallyRunning_returnsTrue(
    core_service: _CoreService, mocker: plugin.MockerFixture
) -> None:
    """A service can become healthy during the retry window."""
    docker_service = _set_service_tasks(core_service, mocker, [])
    running_tasks = [
        {"Status": {"State": "running", "ContainerStatus": {"ContainerID": "abc"}}}
    ]
    docker_service.tasks.side_effect = [[], running_tasks, running_tasks]

    assert core_service.is_service_healthy() is True


@pytest.mark.parametrize("missing_service", [False, True])
def testAgentServiceReadiness_whenRetriesExhausted_returnsFalse(
    runtime_instance: _Runtime, mocker: plugin.MockerFixture, missing_service: bool
) -> None:
    """Unhealthy and removed Docker services cannot become truthy retry Futures."""
    service = _agent_service(mocker)
    if missing_service:
        service.tasks.side_effect = docker.errors.NotFound("removed")

    assert runtime_instance._is_service_healthy(service) is False
    assert service.tasks.call_count == 20


def testAgentReadiness_whenRetriesExhausted_usesOneServiceRetryBudget(
    runtime_instance: _Runtime, mocker: plugin.MockerFixture
) -> None:
    """An unhealthy agent gets one bounded service readiness window."""
    service = _agent_service(mocker)
    mocker.patch.object(
        runtime_instance, "_list_agent_services", return_value=[service]
    )

    assert runtime_instance._are_agents_ready() is False
    assert service.tasks.call_count == 20


def testAgentReadiness_whenEventuallyRunning_returnsTrue(
    runtime_instance: _Runtime, mocker: plugin.MockerFixture
) -> None:
    """An agent can recover on the final poll within its readiness window."""
    service = _agent_service(mocker)
    service.tasks.side_effect = [[]] * 19 + [[{"Status": {"State": "running"}}]]
    mocker.patch.object(
        runtime_instance, "_list_agent_services", return_value=[service]
    )

    assert runtime_instance._are_agents_ready() is True
    assert service.tasks.call_count == 20


@pytest.mark.parametrize("tracing", [False, True])
def testCoreReadiness_whenHealthy_returnsTrue(
    mocker: plugin.MockerFixture, tracing: bool
) -> None:
    """Successful local core readiness explicitly returns True."""
    runtime = local_runtime.LocalRuntime(tracing=tracing)
    runtime._mq_service = mocker.Mock()
    runtime._redis_service = mocker.Mock()
    runtime._jaeger_service = mocker.Mock()
    for service in [
        runtime._mq_service,
        runtime._redis_service,
        runtime._jaeger_service,
    ]:
        service.is_service_healthy.return_value = True

    assert runtime._are_services_ready() is True


def testLocalScan_whenCoreRetriesExhausted_setsErrorAndCleansUp(
    core_service: _CoreService, mocker: plugin.MockerFixture
) -> None:
    """An exhausted core service aborts startup and records ERROR before cleanup."""
    docker_service = _set_service_tasks(core_service, mocker, [])
    docker_service.attrs = {"Spec": {"Labels": {"ostorlab.universe": "1"}}}
    runtime = local_runtime.LocalRuntime(
        scan_id="1", run_default_agents=False, tracing=True
    )
    runtime._docker_client = mocker.MagicMock()
    _mock_cleanup_resources(runtime._docker_client, docker_service)
    runtime._mq_service = (
        core_service if isinstance(core_service, mq.LocalRabbitMQ) else mocker.Mock()
    )
    runtime._redis_service = (
        core_service if isinstance(core_service, redis.LocalRedis) else mocker.Mock()
    )
    runtime._jaeger_service = (
        core_service if isinstance(core_service, jaeger.LocalJaeger) else mocker.Mock()
    )
    mocker.patch.object(runtime, "_create_network")
    mocker.patch.object(runtime, "_start_services")
    start_agents = mocker.patch.object(runtime, "_start_agents")
    mocker.patch.object(runtime, "_wait_log_streamer")
    cleanup = mocker.spy(runtime, "cleanup")

    with pytest.raises(local_runtime.UnhealthyService):
        runtime.scan("test", definitions.AgentGroupDefinition(agents=[]), assets=None)

    with models.Database() as session:
        scan = session.get(models.Scan, runtime._scan_db.id)
        assert scan.progress == models.ScanProgress.ERROR
    start_agents.assert_not_called()
    cleanup.assert_called_once_with()
    docker_service.remove.assert_called_once_with()


def testScan_whenAgentRetriesExhausted_cleansUpWithoutInjectingAssets(
    runtime_instance: _Runtime, mocker: plugin.MockerFixture
) -> None:
    """Both runtimes abort asset injection and clean up unhealthy agent scans."""
    service = _agent_service(mocker)
    mocker.patch.object(
        runtime_instance, "_list_agent_services", return_value=[service]
    )
    mocker.patch.object(runtime_instance, "_start_agents")
    inject = mocker.patch.object(runtime_instance, "_inject_assets")
    if isinstance(runtime_instance, local_runtime.LocalRuntime):
        runtime_instance._docker_client = mocker.MagicMock()
        mocker.patch.object(runtime_instance, "_create_network")
        mocker.patch.object(runtime_instance, "_start_services")
        mocker.patch.object(
            runtime_instance, "_check_services_healthy", return_value=True
        )
        mocker.patch.object(runtime_instance, "_wait_log_streamer")
        _mock_cleanup_resources(runtime_instance._docker_client, service)
        cleanup = mocker.spy(runtime_instance, "cleanup")
        with pytest.raises(local_runtime.AgentNotHealthy):
            runtime_instance.scan(
                "test",
                definitions.AgentGroupDefinition(agents=[]),
                assets=[ipv4.IPv4(host="8.8.8.8", mask="32")],
            )
        with models.Database() as session:
            scan = session.get(models.Scan, runtime_instance._scan_db.id)
            assert scan.progress == models.ScanProgress.ERROR
        cleanup.assert_called_once_with()
    else:
        _mock_cleanup_resources(runtime_instance._docker_client, service)
        cleanup = mocker.spy(runtime_instance, "stop")
        runtime_instance.scan(
            "test",
            definitions.AgentGroupDefinition(agents=[]),
            assets=[ipv4.IPv4(host="8.8.8.8", mask="32")],
        )
        cleanup.assert_called_once_with(runtime_instance.scan_id)
    inject.assert_not_called()
    service.remove.assert_called_once_with()
