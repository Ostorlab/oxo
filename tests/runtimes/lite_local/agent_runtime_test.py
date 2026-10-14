"""Unittest for lite local agent runtime."""

import docker
from pytest_mock import plugin

from ostorlab.agent import definitions as agent_definitions
from ostorlab.runtimes import definitions
from ostorlab.runtimes.lite_local import agent_runtime


def container_name_mock(name: str) -> str:
    """Return a fixed container image name for the patched AgentSettings property."""
    del name
    return "name"


def testLiteLocalCreateAgentService_always_healthcheckProbesEveryStartIntervalWhileStarting(
    mocker: plugin.MockerFixture,
) -> None:
    """The agent service healthcheck is probed every 2 seconds during a 60 seconds start
    period, then every 60 seconds once the container is healthy."""
    mocker.patch("docker.DockerClient.info", return_value={"Name": "test-host"})
    agent_def = agent_definitions.AgentDefinition(
        name="agent_name_from_def",
        restart_policy="",
        open_ports=[],
    )
    mocker.patch(
        "ostorlab.runtimes.lite_local.agent_runtime.AgentRuntime.create_agent_definition_from_label",
        return_value=agent_def,
    )
    mocker.patch(
        "ostorlab.runtimes.definitions.AgentSettings.container_image",
        property(container_name_mock),
    )
    mocker.patch(
        "ostorlab.runtimes.lite_local.agent_runtime.AgentRuntime.update_agent_settings",
        return_value=None,
    )
    mocker.patch(
        "ostorlab.runtimes.lite_local.agent_runtime.AgentRuntime.create_settings_config",
        return_value=None,
    )
    mocker.patch(
        "ostorlab.runtimes.lite_local.agent_runtime.AgentRuntime.create_definition_config",
        return_value=None,
    )
    create_service_mock = mocker.patch(
        "docker.models.services.ServiceCollection.create", return_value=None
    )
    docker_client = docker.from_env()
    agent_settings = definitions.AgentSettings(key="agent/org/name")
    runtime_agent = agent_runtime.AgentRuntime(
        agent_settings,
        "42",
        docker_client,
        bus_url="bus",
        bus_vhost="/",
        bus_management_url="mgmt",
        bus_exchange_topic="topic",
        redis_url="redis://redis",
        tracing_collector_url="jaeger://localhost/",
        labels={},
    )

    runtime_agent.create_agent_service(network_name="test", extra_configs=[])

    healthcheck = create_service_mock.call_args.kwargs["healthcheck"]
    assert healthcheck["StartPeriod"] == 60 * 1000000000
    assert healthcheck["StartInterval"] == 2 * 1000000000
    assert healthcheck["Interval"] == 60 * 1000000000
