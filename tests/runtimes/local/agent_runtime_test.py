"""Unittest for agent runtime."""

import docker
import pytest
from pytest_mock import plugin

import ostorlab
from ostorlab.agent import definitions as agent_definitions
from ostorlab.runtimes import definitions
from ostorlab.runtimes.local import agent_runtime
from ostorlab.utils import definitions as utils_defintions


def container_name_mock(name):
    del name
    return "complex_long_name_special_duplicate_agent:v1026"


def testCreateAgentService_whenAgentDefAndAgentSettingsAreNotEmpty_serviceCreatedWithAgentSettings(
    mocker: plugin.MockerFixture,
) -> None:
    """Test creation of the agent service : Case where agent definitions & agent settings have different values for
    some attributes, the agent settings values should override.
    """
    agent_def = agent_definitions.AgentDefinition(
        name="agent_name_from_def",
        mounts=["def_mount1", "def_mount2"],
        mem_limit=420000,
        restart_policy="",
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
        labels={},
    )
    runtime_agent.create_agent_service(network_name="test", extra_configs=[])

    kwargs = create_service_mock.call_args.kwargs

    # assert arguments were overridden by the agent settings.
    assert kwargs["resources"]["Limits"]["MemoryBytes"] == 700000
    assert len(kwargs["name"]) < 63
    assert "complex_long_name_special_duplicate_agent_42" in kwargs["name"]
    assert kwargs["mounts"] == ["settings_mount1"]
    assert kwargs["endpoint_spec"]["Ports"][0]["PublishedPort"] == 40000
    assert kwargs["restart_policy"]["Condition"] == "on-failure"
    assert kwargs["container_labels"] == {"ostorlab.scan_id": "42"}


def testCreateAgentService_whenAgentDefIsNotEmptyAndAgentSettingsIsEmpty_serviceCreatedWithAgentDef(
    mocker: plugin.MockerFixture,
) -> None:
    """Test creation of the agent service : Case where agent settings values are empty,
    the agent definition values should be used.
    """
    agent_def = agent_definitions.AgentDefinition(
        name="agent_name_from_def",
        mounts=["def_mount1", "def_mount2"],
        mem_limit=620000,
        restart_policy="",
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
        labels={},
    )
    runtime_agent.create_agent_service(network_name="test", extra_configs=[])

    kwargs = create_service_mock.call_args.kwargs

    # assert arguments from agent definition were used.
    assert kwargs["resources"]["Limits"]["MemoryBytes"] == 620000
    assert kwargs["mounts"] == ["def_mount1", "def_mount2"]
    assert kwargs["endpoint_spec"]["Ports"][0]["PublishedPort"] == 30000
    assert kwargs["restart_policy"]["Condition"] == "any"


def testCreateAgentService_whenReplicasIsProvided_serviceCreatedWithReplicas(
    mocker: plugin.MockerFixture,
) -> None:
    """Test creation of the agent service : Case where agent definitions & agent settings have different values for
    some attributes, the agent settings values should override.
    """
    agent_def = agent_definitions.AgentDefinition(
        name="agent_name_from_def",
        mounts=["def_mount1", "def_mount2"],
        mem_limit=420000,
        restart_policy="",
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
        labels={},
    )
    runtime_agent.create_agent_service(
        network_name="test", extra_configs=[], replicas=3
    )

    kwargs = create_service_mock.call_args.kwargs
    assert kwargs["mode"] == {"replicated": {"Replicas": 3}}


def testCreateAgentService_whenServiceNameProvidedInAgentDefinition_serviceCreatedWithServiceName(
    mocker: plugin.MockerFixture,
) -> None:
    """Test creation of the agent service : Case where agent definitions has a service name defined."""
    agent_def = agent_definitions.AgentDefinition(
        name="agent_name_from_def",
        service_name="custom_service_name",
        mounts=["def_mount1", "def_mount2"],
        mem_limit=420000,
        restart_policy="",
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
    agent_settings = definitions.AgentSettings(
        key="agent/org/name",
        mounts=["settings_mount1"],
        mem_limit=700000,
        restart_policy="on-failure",
        constraints=["constraint1"],
    )
    runtime_agent = agent_runtime.AgentRuntime(
        agent_settings,
        "42",
        docker_client,
        mq_service=None,
        redis_service=None,
        jaeger_service=None,
        labels={},
    )
    runtime_agent.create_agent_service(network_name="test", extra_configs=[])

    kwargs = create_service_mock.call_args.kwargs

    assert kwargs["resources"]["Limits"]["MemoryBytes"] == 700000
    assert kwargs["mounts"] == ["settings_mount1"]
    assert kwargs["endpoint_spec"]["Ports"][0]["PublishedPort"] == 30000
    assert kwargs["restart_policy"]["Condition"] == "on-failure"
    assert kwargs["name"] == "custom_service_name"


def testCreateAgentService_whenServiceNameProvidedInAgentDefinitionAndTooLong_raiseServiceNameTooLongException(
    mocker: plugin.MockerFixture,
) -> None:
    """Test creation of the agent service : Case where agent definitions has a service name defined but too long."""
    agent_def = agent_definitions.AgentDefinition(
        name="agent_name_from_def",
        service_name="c" * 100,
        mounts=["def_mount1", "def_mount2"],
        mem_limit=420000,
        restart_policy="",
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
    agent_settings = definitions.AgentSettings(
        key="agent/org/name",
        mounts=["settings_mount1"],
        mem_limit=700000,
        restart_policy="on-failure",
        constraints=["constraint1"],
    )
    runtime_agent = agent_runtime.AgentRuntime(
        agent_settings,
        "42",
        docker_client,
        mq_service=None,
        redis_service=None,
        jaeger_service=None,
    )
    with pytest.raises(agent_runtime.ServiceNameTooLong):
        runtime_agent.create_agent_service(network_name="test", extra_configs=[])

    assert create_service_mock.call_count == 0


def testCreateAgentService_whenServiceNameProvidedInAgentSettings_overridesAgentDefinitionServiceName(
    mocker: plugin.MockerFixture,
) -> None:
    """Test that service_name from AgentSettings (YAML) takes precedence over the image label service_name."""
    agent_def = agent_definitions.AgentDefinition(
        name="crawler",
        service_name="crawler",
        mounts=[],
        mem_limit=None,
        restart_policy="",
        open_ports=[],
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
    agent_settings = definitions.AgentSettings(
        key="agent/ostorlab/crawler",
        service_name="crawler_bus",
        restart_policy="on-failure",
        constraints=[],
        mounts=[],
        open_ports=[],
    )
    runtime_agent = agent_runtime.AgentRuntime(
        agent_settings,
        "42",
        docker_client,
        mq_service=None,
        redis_service=None,
        jaeger_service=None,
        labels={},
    )
    runtime_agent.create_agent_service(network_name="test", extra_configs=[])

    kwargs = create_service_mock.call_args.kwargs
    assert kwargs["name"] == "crawler_bus"


def testCreateAgentService_whenNoExplicitServiceName_serviceKeyLabelIsAgentName(
    mocker: plugin.MockerFixture,
) -> None:
    """Service key label should be the agent's logical name when no explicit service name is set."""
    agent_def = agent_definitions.AgentDefinition(
        name="nuclei",
        mounts=[],
        mem_limit=None,
        restart_policy="",
        open_ports=[],
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
    agent_settings = definitions.AgentSettings(key="agent/ostorlab/nuclei")
    runtime_agent = agent_runtime.AgentRuntime(
        agent_settings,
        "42",
        docker_client,
        mq_service=None,
        redis_service=None,
        jaeger_service=None,
        labels={},
    )
    runtime_agent.create_agent_service(network_name="test", extra_configs=[])

    kwargs = create_service_mock.call_args.kwargs
    assert kwargs["labels"]["ostorlab.queue_name"] == "nuclei"


def testCreateAgentService_whenExplicitServiceName_serviceKeyLabelIsServiceName(
    mocker: plugin.MockerFixture,
) -> None:
    """Service key label should be the explicit service name (e.g. crawler_bus) when set."""
    agent_def = agent_definitions.AgentDefinition(
        name="crawler",
        service_name="crawler",
        mounts=[],
        mem_limit=None,
        restart_policy="",
        open_ports=[],
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
    agent_settings = definitions.AgentSettings(
        key="agent/ostorlab/crawler",
        service_name="crawler_bus",
    )
    runtime_agent = agent_runtime.AgentRuntime(
        agent_settings,
        "42",
        docker_client,
        mq_service=None,
        redis_service=None,
        jaeger_service=None,
        labels={},
    )
    runtime_agent.create_agent_service(network_name="test", extra_configs=[])

    kwargs = create_service_mock.call_args.kwargs
    assert kwargs["labels"]["ostorlab.queue_name"] == "crawler_bus"


def testCreateAgentService_whenImageNameTooLongForRandomSuffix_serviceNameTruncatedToFitSuffix(
    mocker: plugin.MockerFixture,
) -> None:
    """When the base service name is too long to append a random suffix, the base is truncated so the suffix always fits."""
    agent_def = agent_definitions.AgentDefinition(
        name="agent_name_from_def",
        mounts=[],
        mem_limit=None,
        restart_policy="",
        open_ports=[],
    )
    mocker.patch(
        "ostorlab.runtimes.local.agent_runtime.AgentRuntime.create_agent_definition_from_label",
        return_value=agent_def,
    )
    mocker.patch.object(
        ostorlab.runtimes.definitions.AgentSettings,
        "container_image",
        property(lambda name: "a" * 70 + ":latest"),
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
    mocker.patch(
        "ostorlab.runtimes.local.agent_runtime.random.randrange", return_value=1234
    )
    create_service_mock = mocker.patch(
        "docker.models.services.ServiceCollection.create", return_value=None
    )

    docker_client = docker.from_env()
    agent_settings = definitions.AgentSettings(
        key="agent/ostorlab/test",
        restart_policy="on-failure",
        constraints=[],
        mounts=[],
        open_ports=[],
    )
    runtime_agent = agent_runtime.AgentRuntime(
        agent_settings,
        "scanner0",
        docker_client,
        mq_service=None,
        redis_service=None,
        jaeger_service=None,
        labels={},
    )
    runtime_agent.create_agent_service(network_name="test", extra_configs=[])

    kwargs = create_service_mock.call_args.kwargs
    assert len(kwargs["name"]) <= 63
    assert kwargs["name"].endswith("_1234")


def testCreateAgentService_whenServiceNameIsSet_serviceNameInjectedAsEnvVar(
    mocker: plugin.MockerFixture,
) -> None:
    """SERVICE_NAME env var must equal the docker service name so agents can label GCP logs."""
    agent_def = agent_definitions.AgentDefinition(
        name="agent_name_from_def",
        service_name="my_explicit_service",
        mounts=[],
        mem_limit=420000,
        restart_policy="",
        open_ports=[],
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

    docker_client = mocker.MagicMock()
    agent_settings = definitions.AgentSettings(key="agent/org/name")
    runtime_agent = agent_runtime.AgentRuntime(
        agent_settings,
        "42",
        docker_client,
        mq_service=None,
        redis_service=None,
        jaeger_service=None,
        labels={},
    )
    runtime_agent.create_agent_service(network_name="test", extra_configs=[])

    kwargs = docker_client.services.create.call_args.kwargs
    service_name = kwargs["name"]
    assert f"SERVICE_NAME={service_name}" in kwargs["env"]


def testCreateAgentService_whenServiceNameIsSet_addsMachineNameAsEnvVar(
    mocker,
):
    """Test creation of the agent service includes HOST_HOSTNAME in env."""
    mock_host_hostname = "test-mocked-hostname"
    mocker.patch("docker.DockerClient.info", return_value={"Name": mock_host_hostname})
    agent_def = agent_definitions.AgentDefinition(
        name="agent_name_from_def",
        mounts=["def_mount1"],
        mem_limit=420000,
        service_name="test",
        restart_policy="",
    )
    mocker.patch(
        "ostorlab.runtimes.local.agent_runtime.AgentRuntime.create_agent_definition_from_label",
        return_value=agent_def,
    )
    mocker.patch(
        "ostorlab.runtimes.local.agent_runtime.AgentRuntime.update_agent_settings"
    )
    mocker.patch(
        "ostorlab.runtimes.local.agent_runtime.AgentRuntime.create_settings_config"
    )
    mocker.patch(
        "ostorlab.runtimes.local.agent_runtime.AgentRuntime.create_definition_config"
    )
    mocker.patch(
        "ostorlab.runtimes.definitions.AgentSettings.container_image",
        new_callable=mocker.PropertyMock,
    )
    create_service_mock = mocker.patch(
        "docker.models.services.ServiceCollection.create", return_value=None
    )
    mock_docker_client = docker.from_env()
    agent_settings = definitions.AgentSettings(key="agent/org/name")
    runtime_agent = agent_runtime.AgentRuntime(
        agent_settings,
        "42",
        mock_docker_client,
        mq_service=None,
        redis_service=None,
        jaeger_service=None,
        labels={},
    )

    runtime_agent.create_agent_service(
        network_name="test", extra_configs=[], replicas=3
    )

    create_service_mock.assert_called_once()
    kwargs = create_service_mock.call_args.kwargs
    env_vars = kwargs.get("env", [])
    assert kwargs.get("mode") == {"replicated": {"Replicas": 3}}
    assert any(env.startswith("UNIVERSE") for env in env_vars), (
        "UNIVERSE not found in env variables"
    )
    assert f"HOST_HOSTNAME={mock_host_hostname}" in env_vars


def testCreateAgentService_whenContainerLabelsProvided_mergesIntoContainerLabels(
    mocker: plugin.MockerFixture,
) -> None:
    """Container labels should be merged into the container_labels dict when provided."""
    agent_def = agent_definitions.AgentDefinition(
        name="agent_name_from_def",
        mounts=[],
        mem_limit=None,
        restart_policy="",
        open_ports=[],
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
        "ostorlab.runtimes.local.agent_runtime.AgentRuntime.update_agent_settings"
    )
    mocker.patch(
        "ostorlab.runtimes.local.agent_runtime.AgentRuntime.create_settings_config"
    )
    mocker.patch(
        "ostorlab.runtimes.local.agent_runtime.AgentRuntime.create_definition_config"
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
        labels={"ostorlab.reference_scan_id": "ref-123"},
    )
    runtime_agent.create_agent_service(network_name="test", extra_configs=[])

    kwargs = create_service_mock.call_args.kwargs
    assert kwargs["container_labels"]["ostorlab.reference_scan_id"] == "ref-123"
    assert kwargs["container_labels"]["ostorlab.scan_id"] == "42"


def testCreateScanVolumeMounts_whenVolumeIsMissing_createsSharedScanVolumeMounts(
    mocker: plugin.MockerFixture,
) -> None:
    """Missing shared scan volumes should be created and mounted per scan."""
    mock_docker_client = mocker.MagicMock()
    mock_docker_client.info.return_value = {"Name": "host"}
    mock_docker_client.volumes.get.side_effect = [
        docker.errors.NotFound("missing"),
        mocker.MagicMock(),
    ]
    create_volume_mock = mock_docker_client.volumes.create
    mocker.patch.object(
        ostorlab.runtimes.definitions.AgentSettings,
        "container_image",
        property(container_name_mock),
    )
    mocker.patch(
        "ostorlab.runtimes.local.agent_runtime.AgentRuntime.update_agent_settings",
        return_value=None,
    )
    mount_mock = mocker.patch(
        "ostorlab.runtimes.local.agent_runtime.docker_types_services.Mount",
        side_effect=["mount-1", "mount-2"],
    )

    runtime_agent = agent_runtime.AgentRuntime(
        ostorlab.runtimes.definitions.AgentSettings(key="agent/org/name"),
        "scan-42",
        mock_docker_client,
        mq_service=None,
        redis_service=None,
        jaeger_service=None,
        labels={},
    )

    mounts = runtime_agent.create_scan_volume_mounts(
        [
            utils_defintions.Volume(
                name="repository_code", path="/code", read_only=False
            ),
            utils_defintions.Volume(name="shared_cache", path="/cache"),
        ]
    )

    assert mounts == ["mount-1", "mount-2"]
    mock_docker_client.volumes.get.assert_any_call("repository_code_scan-42")
    mock_docker_client.volumes.get.assert_any_call("shared_cache_scan-42")
    create_volume_mock.assert_called_once_with(
        name="repository_code_scan-42",
        labels={"ostorlab.universe": "scan-42"},
    )
    assert mount_mock.call_args_list[0].kwargs == {
        "target": "/code",
        "source": "repository_code_scan-42",
        "type": "volume",
        "read_only": False,
    }
