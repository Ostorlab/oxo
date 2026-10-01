"""Readiness retries must return booleans and prevent unhealthy scans."""

import unittest.mock

import docker
import pytest
import tenacity
from docker.models import configs
from docker.models import containers
from docker.models import services
from pytest_mock import plugin

from ostorlab.assets import asset as base_asset
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
    mocker.patch.object(runtime_type, "_start_agents")
    if runtime_type is local_runtime.LocalRuntime:
        mocker.patch.object(runtime_type, "_create_network")
        mocker.patch.object(runtime_type, "_start_services")
        mocker.patch.object(runtime_type, "_check_services_healthy", return_value=True)
        mocker.patch.object(runtime_type, "_wait_log_streamer")
        runtime = runtime_type(scan_id="1", run_default_agents=False)
        runtime.can_run(definitions.AgentGroupDefinition(agents=[]))
        return runtime
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


def _assert_scan_progress(scan_id: int, progress: models.ScanProgress) -> None:
    with models.Database() as session:
        scan = session.get(models.Scan, scan_id)
        assert scan is not None
        assert scan.progress == progress


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


def testScan_whenAgentRecoversOnFinalPoll_injectsAssets(
    runtime_instance: _Runtime, mocker: plugin.MockerFixture
) -> None:
    """An agent recovering on poll twenty permits public scan startup."""
    service = _agent_service(mocker)
    service.tasks.side_effect = [[]] * 19 + [[{"Status": {"State": "running"}}]]
    assert runtime_instance._docker_client is not None
    runtime_instance._docker_client.services.list.return_value = [service]
    inject = mocker.patch.object(runtime_instance, "_inject_assets")
    cleanup = mocker.spy(runtime_instance, "cleanup")
    assets: list[base_asset.Asset] = [ipv4.IPv4(host="8.8.8.8", mask="32")]

    scan = runtime_instance.scan(
        "test", definitions.AgentGroupDefinition(agents=[]), assets=assets
    )

    assert service.tasks.call_count == 20
    inject.assert_called_once_with(assets=assets, agent_settings=None)
    cleanup.assert_not_called()
    service.remove.assert_not_called()
    if isinstance(runtime_instance, local_runtime.LocalRuntime):
        assert scan is not None
        _assert_scan_progress(scan.id, models.ScanProgress.IN_PROGRESS)


@pytest.mark.parametrize("tracing", [False, True])
def testLocalScan_whenCoreServicesHealthy_injectsAssetsAndSetsInProgress(
    mocker: plugin.MockerFixture, tracing: bool
) -> None:
    """Healthy core services permit scan startup with either tracing setting."""
    mocker.patch("docker.from_env", return_value=mocker.MagicMock())
    runtime = local_runtime.LocalRuntime(
        scan_id="1", run_default_agents=False, tracing=tracing
    )
    runtime._docker_client = mocker.MagicMock()
    runtime._docker_client.services.list.return_value = []
    runtime._mq_service = mq.LocalRabbitMQ(name="1", network="network")
    runtime._redis_service = redis.LocalRedis(name="1", network="network")
    runtime._jaeger_service = jaeger.LocalJaeger(name="1", network="network")
    running_tasks: list[dict[str, object]] = [
        {"Status": {"State": "running", "ContainerStatus": {"ContainerID": "abc"}}}
    ]
    core_services: list[_CoreService] = [
        runtime._mq_service,
        runtime._redis_service,
        runtime._jaeger_service,
    ]
    for service in core_services:
        _set_service_tasks(service, mocker, running_tasks)
    mocker.patch.object(runtime, "_create_network")
    mocker.patch.object(runtime, "_start_services")
    mocker.patch.object(runtime, "_wait_log_streamer")
    inject = mocker.patch.object(runtime, "_inject_assets")
    cleanup = mocker.spy(runtime, "cleanup")
    assets: list[base_asset.Asset] = [ipv4.IPv4(host="8.8.8.8", mask="32")]

    scan = runtime.scan(
        "test", definitions.AgentGroupDefinition(agents=[]), assets=assets
    )

    assert scan is not None
    _assert_scan_progress(scan.id, models.ScanProgress.IN_PROGRESS)
    inject.assert_called_once_with(assets=assets, agent_settings=None)
    cleanup.assert_not_called()


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
    prepared_scan = runtime.prepare_scan("test")

    with pytest.raises(local_runtime.UnhealthyService):
        runtime.scan("test", definitions.AgentGroupDefinition(agents=[]), assets=None)

    _assert_scan_progress(prepared_scan.id, models.ScanProgress.ERROR)
    start_agents.assert_not_called()
    cleanup.assert_called_once_with()
    docker_service.remove.assert_called_once_with()


@pytest.mark.parametrize("missing_service", [False, True])
def testScan_whenAgentRetriesExhausted_cleansUpWithoutInjectingAssets(
    runtime_instance: _Runtime, mocker: plugin.MockerFixture, missing_service: bool
) -> None:
    """Both runtimes abort asset injection and clean up unhealthy agent scans."""
    service = _agent_service(mocker)
    if missing_service is True:
        service.tasks.side_effect = docker.errors.NotFound("removed")
    assert runtime_instance._docker_client is not None
    _mock_cleanup_resources(runtime_instance._docker_client, service)
    inject = mocker.patch.object(runtime_instance, "_inject_assets")
    if isinstance(runtime_instance, local_runtime.LocalRuntime):
        prepared_scan = runtime_instance.prepare_scan("test")
        cleanup = mocker.spy(runtime_instance, "cleanup")
        with pytest.raises(local_runtime.AgentNotHealthy):
            runtime_instance.scan(
                "test",
                definitions.AgentGroupDefinition(agents=[]),
                assets=[ipv4.IPv4(host="8.8.8.8", mask="32")],
            )
        _assert_scan_progress(prepared_scan.id, models.ScanProgress.ERROR)
        cleanup.assert_called_once_with()
    else:
        cleanup = mocker.spy(runtime_instance, "stop")
        with pytest.raises(lite_runtime.AgentNotHealthy):
            runtime_instance.scan(
                "test",
                definitions.AgentGroupDefinition(agents=[]),
                assets=[ipv4.IPv4(host="8.8.8.8", mask="32")],
            )
        cleanup.assert_called_once_with(runtime_instance.scan_id)
    inject.assert_not_called()
    service.remove.assert_called_once_with()
    assert service.tasks.call_count == 20


@pytest.mark.parametrize(
    ("service_type", "service_index", "service_name"),
    [
        (mq.LocalRabbitMQ, 0, "MQ"),
        (redis.LocalRedis, 1, "Redis"),
        (jaeger.LocalJaeger, 2, "Jaeger"),
    ],
)
def testLocalScan_whenCoreServiceCreationFails_skipsReadinessAndCleansUp(
    offline_docker_client: docker.DockerClient,
    mocker: plugin.MockerFixture,
    service_type: type[_CoreService],
    service_index: int,
    service_name: str,
) -> None:
    """A failed core creation aborts before polling, agents or asset injection."""
    runtime = local_runtime.LocalRuntime(
        scan_id="1", run_default_agents=False, tracing=True
    )
    runtime._docker_client = offline_docker_client
    docker_services = [
        services.Service(
            attrs={
                "ID": name,
                "Spec": {"Name": name, "Labels": {"ostorlab.universe": "1"}},
            },
            client=offline_docker_client,
        )
        for name in ["mq_1", "redis_1", "jaeger_1"]
    ]
    creations: list[services.Service | docker.errors.APIError] = list(docker_services)
    creations[service_index] = docker.errors.APIError("creation failed")
    mocker.patch.object(
        services.ServiceCollection, "create", autospec=True, side_effect=creations
    )
    mocker.patch.object(
        services.ServiceCollection,
        "list",
        autospec=True,
        return_value=[s for i, s in enumerate(docker_services) if i != service_index],
    )
    remove = mocker.patch.object(services.Service, "remove", autospec=True)
    mocker.patch.object(
        services.Service,
        "tasks",
        autospec=True,
        return_value=[
            {"Status": {"State": "running", "ContainerStatus": {"ContainerID": "abc"}}}
        ],
    )
    mocker.patch(
        "docker.models.networks.NetworkCollection.list", autospec=True, return_value=[]
    )
    mocker.patch("docker.models.networks.NetworkCollection.create", autospec=True)
    mocker.patch.object(
        configs.ConfigCollection,
        "get",
        autospec=True,
        side_effect=docker.errors.NotFound("no config"),
    )
    mocker.patch.object(
        configs.ConfigCollection,
        "create",
        autospec=True,
        return_value=configs.Config(attrs={"ID": "config"}),
    )
    mocker.patch.object(
        configs.ConfigCollection, "list", autospec=True, return_value=[]
    )
    mocker.patch(
        "docker.models.volumes.VolumeCollection.list", autospec=True, return_value=[]
    )
    mocker.patch(
        "docker.models.volumes.VolumeCollection.get",
        autospec=True,
        side_effect=docker.errors.NotFound("no volume"),
    )
    mocker.patch.object(
        containers.ContainerCollection,
        "get",
        autospec=True,
        return_value=containers.Container(attrs={"Id": "abc"}),
    )
    mocker.patch.object(
        containers.Container,
        "exec_run",
        autospec=True,
        return_value=containers.ExecResult(0, b""),
    )
    mocker.patch("click.launch", autospec=True)
    mocker.patch.object(
        service_type,
        "is_service_healthy",
        service_type.is_service_healthy.retry_with(wait=tenacity.wait_none()),
    )
    health_check = mocker.spy(service_type, "is_service_healthy")
    start_agents = mocker.patch.object(runtime, "_start_agents")
    inject = mocker.patch.object(runtime, "_inject_assets")
    cleanup = mocker.spy(runtime, "cleanup")
    prepared_scan = runtime.prepare_scan("test")

    with pytest.raises(local_runtime.UnhealthyService, match=service_name):
        runtime.scan(
            "test",
            definitions.AgentGroupDefinition(agents=[]),
            assets=[ipv4.IPv4(host="8.8.8.8", mask="32")],
        )

    _assert_scan_progress(prepared_scan.id, models.ScanProgress.ERROR)
    cleanup.assert_called_once_with()
    assert remove.call_count == 2
    start_agents.assert_not_called()
    inject.assert_not_called()
    health_check.assert_not_called()
