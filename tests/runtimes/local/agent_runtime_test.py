"""Unittest for agent runtime."""
import docker

from ostorlab.agent import definitions as agent_definitions
from ostorlab.runtimes import definitions
from ostorlab.runtimes.local import agent_runtime
from ostorlab.utils import defintions as utils_defintions

import ostorlab

def container_name_mock(name):
    del name
    return "name"


def testCreateAgentService_whenAgentDefAndAgentSettingsAreNotEmpty_serviceCreatedwithAgentSettings(
    mocker,
):
    """Test creation of the agent service : Case where agent definitions & agent settings have different values for
    some attributes, the agent settings values should override.
    """
    agent_def = agent_definitions.AgentDefinition(
        name="agent_name_from_def",
        mounts=["def_mount1", "def_mount2"],
        mem_limit=420000,
        restart_policy="any",
        open_ports=[
            utils_defintions.PortMapping(20000, 30000),
            utils_defintions.PortMapping(20001, 30001),
        ],
    )
    mocker.patch(
        "ostorlab.runtimes.local.agent_runtime.AgentRuntime.create_agent_definition_from_label",
        return_value=agent_def,
    )
    mocker.patch.object(
        ostorlab.runtimes.definitions.AgentSettings,
        "container_image",
        property(container_name_mock),
    )
    mocker.patch(
        "ostorlab.runtimes.local.agent_runtime.AgentRuntime.update_agent_settings",
        return_value=None,
    )
    mocker.patch(
        "ostorlab.runtimes.local.agent_runtime.AgentRuntime.create_settings_config",
        return_value=None,
    )
    mocker.patch(
        "ostorlab.runtimes.local.agent_runtime.AgentRuntime.create_definition_config",
        return_value=None,
    )
    create_service_mock = mocker.patch(
        "docker.models.services.ServiceCollection.create", return_value=None
    )

    docker_client = docker.from_env()
    settings_open_ports = [
        utils_defintions.PortMapping(20000, 40000),
        utils_defintions.PortMapping(20002, 40002),
    ]
    agent_settings = definitions.AgentSettings(
        key="agent/org/name",
        mounts=["settings_mount1"],
        mem_limit=700000,
        restart_policy="on-failure",
        constraints=["constraint1"],
        open_ports=settings_open_ports,
    )

    runtime_agent = agent_runtime.AgentRuntime(
        agent_settings,
        "42",
        docker_client,
        mq_service=None,
        redis_service=None,
        jaeger_service=None,
    )
    runtime_agent.create_agent_service(network_name="test", extra_configs=[])

    kwargs = create_service_mock.call_args.kwargs

    # assert arguments were overridden by the agent settings.
    assert kwargs["resources"]["Limits"]["MemoryBytes"] == 700000
    assert kwargs["mounts"] == ["settings_mount1"]
    assert kwargs["endpoint_spec"]["Ports"][0]["PublishedPort"] == 40000
    assert kwargs["restart_policy"]["Condition"] == "on-failure"


def testCreateAgentService_whenAgentDefIsNotEmptyAndAgentSettingsIsEmpty_serviceCreatedwithAgentDef(
    mocker,
):
    """Test creation of the agent service : Case where agent settings values are empty,
    the agent definition values should be used.
    """
    agent_def = agent_definitions.AgentDefinition(
        name="agent_name_from_def",
        mounts=["def_mount1", "def_mount2"],
        mem_limit=620000,
        restart_policy="any",
        open_ports=[
            utils_defintions.PortMapping(20000, 30000),
            utils_defintions.PortMapping(20001, 30001),
        ],
    )
    mocker.patch(
        "ostorlab.runtimes.local.agent_runtime.AgentRuntime.create_agent_definition_from_label",
        return_value=agent_def,
    )
    mocker.patch.object(
        ostorlab.runtimes.definitions.AgentSettings,
        "container_image",
        property(container_name_mock),
    )
    mocker.patch(
        "ostorlab.runtimes.local.agent_runtime.AgentRuntime.update_agent_settings",
        return_value=None,
    )
    mocker.patch(
        "ostorlab.runtimes.local.agent_runtime.AgentRuntime.create_settings_config",
        return_value=None,
    )
    mocker.patch(
        "ostorlab.runtimes.local.agent_runtime.AgentRuntime.create_definition_config",
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
        mq_service=None,
        redis_service=None,
        jaeger_service=None,
    )
    runtime_agent.create_agent_service(network_name="test", extra_configs=[])

    kwargs = create_service_mock.call_args.kwargs

    # assert arguments from agent definition were used.
    assert kwargs["resources"]["Limits"]["MemoryBytes"] == 620000
    assert kwargs["mounts"] == ["def_mount1", "def_mount2"]
    assert kwargs["endpoint_spec"]["Ports"][0]["PublishedPort"] == 30000
    assert kwargs["restart_policy"]["Condition"] == "any"
