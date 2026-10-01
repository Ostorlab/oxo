"""Lite startup must clean Docker resources and propagate known failures."""

import pathlib

import docker
import pytest
import tenacity
from pytest_mock import plugin

from ostorlab.assets import ipv4
from ostorlab.cli import docker_requirements_checker
from ostorlab.runtimes import definitions
from ostorlab.runtimes.lite_local import agent_runtime
from ostorlab.runtimes.lite_local import runtime as lite_runtime
from ostorlab.utils import volumes


@pytest.mark.parametrize(
    "failure", ["unhealthy", "notInstalled", "missingLabel", "success"]
)
def testLiteScan_whenStartingAgents_cleansFailureOrInjectsOnSuccess(
    failure: str, mocker: plugin.MockerFixture
) -> None:
    """Real startup, health checks, and cleanup use mocked Docker resources."""
    for name in [
        "is_docker_installed",
        "is_sys_arch_supported",
        "is_user_permitted",
        "is_docker_working",
        "is_swarm_initialized",
    ]:
        mocker.patch.object(docker_requirements_checker, name, return_value=True)
    client = mocker.MagicMock()
    mocker.patch("docker.from_env", return_value=client)
    client.info.return_value = {"Name": "test"}
    image = client.images.get.return_value
    image.tags = ["test:latest"]
    image.labels = (
        {}
        if failure == "missingLabel"
        else {
            "agent_definition": (
                pathlib.Path(__file__).parents[2] / "agent" / "dummyagent.yaml"
            ).read_text()
        }
    )
    service = mocker.MagicMock()
    service.name = "agent_test"
    service.attrs = {
        "Spec": {
            "Labels": {"ostorlab.universe": "123"},
            "Mode": {"Replicated": {"Replicas": 1}},
            "TaskTemplate": {"RestartPolicy": {"Condition": "any"}},
        }
    }
    service.tasks.return_value = (
        [] if failure == "unhealthy" else [{"Status": {"State": "running"}}]
    )
    client.services.create.return_value = service
    client.services.list.return_value = [service]
    resources = []
    for collection in [client.networks, client.configs, client.volumes]:
        resource = mocker.MagicMock()
        resource.attrs = {"Labels": {"ostorlab.universe": "123"}}
        collection.list.return_value = [resource]
        resources.append(resource)
    client.volumes.get.side_effect = docker.errors.NotFound("no volumes")
    client.configs.get.side_effect = docker.errors.NotFound("no config")
    client.configs.create.return_value.id = "config"
    mocker.patch.object(
        lite_runtime.LiteLocalRuntime,
        "_is_service_healthy",
        lite_runtime.LiteLocalRuntime._is_service_healthy.retry_with(
            wait=tenacity.wait_none()
        ),
    )
    create_volume = mocker.patch.object(volumes, "create_volume")
    runtime = lite_runtime.LiteLocalRuntime(
        scan_id="123",
        bus_url="bus",
        bus_vhost="/",
        bus_management_url="mgmt",
        bus_exchange_topic="topic",
        network="network",
        redis_url="redis://redis",
        tracing_collector_url="http://localhost:14268",
    )
    inject = mocker.spy(runtime, "_inject_assets")
    stop = mocker.spy(runtime, "stop")
    mocker.patch(
        "ostorlab.cli.agent_fetcher.get_container_image",
        return_value=None if failure == "notInstalled" else "test:latest",
    )
    agent = definitions.AgentSettings(key="agent/ostorlab/test")
    group = definitions.AgentGroupDefinition(agents=[agent])
    assets = [ipv4.IPv4(host="8.8.8.8", mask="32")]
    if failure == "success":
        assert runtime.scan("test", group, assets) is None
        inject.assert_called_once_with(assets=assets, agent_settings=None)
        create_volume.assert_called_once()
        stop.assert_not_called()
        service.remove.assert_not_called()
        for resource in resources:
            resource.remove.assert_not_called()
    else:
        error_type = {
            "unhealthy": lite_runtime.AgentNotHealthy,
            "notInstalled": lite_runtime.AgentNotInstalled,
            "missingLabel": agent_runtime.MissingAgentDefinitionLabel,
        }[failure]
        with pytest.raises(error_type) as caught:
            runtime.scan("test", group, assets)
        assert caught.value.__cause__ is not None
        assert "123" in str(caught.value)
        stop.assert_called_once_with("123")
        service.remove.assert_called_once_with()
        for resource in resources:
            resource.remove.assert_called_once()
        inject.assert_not_called()
        create_volume.assert_not_called()
