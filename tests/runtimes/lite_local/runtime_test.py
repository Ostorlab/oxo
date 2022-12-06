"""Unittest for lite local runtime."""
import pytest
from docker.models import services as services_model
import docker

from ostorlab.runtimes.lite_local import agent_runtime
from ostorlab.runtimes import definitions
from ostorlab.agent import definitions as agent_definitions
from ostorlab.runtimes.lite_local import runtime as lite_local_runtime
import ostorlab


def container_name_mock(name):
    del name
    return "name"


@pytest.mark.docker
def testRuntimeScanStop_whenScanIdIsValid_RemovesScanService(mocker):
    """Unittest for the scan stop method when there are local scans available.
    Gets the docker services and checks for those with ostorlab.universe
    as one of the labels to find the service with the given scan id.
    Removes the scan service matching the provided id.
    """

    def docker_services():
        """Method for mocking the services list response."""

        services = [
            {
                "ID": "0099i5n1y3gycuekvksyqyxav",
                "CreatedAt": "2021-12-27T13:37:02.795789947Z",
                "Spec": {"Labels": {"ostorlab.universe": "1"}},
            },
            {
                "ID": "0099i5n1y3gycuekvksyqyxav",
                "CreatedAt": "2021-12-27T13:37:02.795789947Z",
                "Spec": {"Labels": {"ostorlab.universe": "9999"}},
            },
        ]

        return [services_model.Service(attrs=service) for service in services]

    mocker.patch(
        "docker.DockerClient.services", return_value=services_model.ServiceCollection()
    )

    mocker.patch("docker.DockerClient.services.list", side_effect=docker_services)
    mocker.patch("docker.models.networks.NetworkCollection.list", return_value=[])
    mocker.patch("docker.models.configs.ConfigCollection.list", return_value=[])

    docker_service_remove = mocker.patch(
        "docker.models.services.Service.remove", return_value=None
    )
    lite_local_runtime.LiteLocalRuntime(
        scan_id="1",
        bus_url="bus",
        bus_vhost="/",
        bus_management_url="mgmt",
        bus_exchange_topic="top",
        network="privnet",
        redis_url="redis://redis",
        tracing_collector_url="jaeger://localhost/",
    ).stop(scan_id="1")

    docker_service_remove.assert_called_once()


@pytest.mark.docker
def testRuntimeScanStop_whenScanIdIsInvalid_DoesNotRemoveAnyService(
    mocker, db_engine_path
):
    """Unittest for the scan stop method when the scan id is invalid.
    Gets the docker services and checks for those with ostorlab.universe
    as one of the labels to find the service with the given scan id.
    Does not remove any service.
    """

    def docker_services():
        """Method for mocking the services list response."""

        services = [
            {
                "ID": "0099i5n1y3gycuekvksyqyxav",
                "CreatedAt": "2021-12-27T13:37:02.795789947Z",
                "Spec": {"Labels": {"ostorlab.universe": "1"}},
            },
            {
                "ID": "0099i5n1y3gycuekvksyqyxav",
                "CreatedAt": "2021-12-27T13:37:02.795789947Z",
                "Spec": {"Labels": {"ostorlab.universe": "2"}},
            },
        ]

        return [services_model.Service(attrs=service) for service in services]

    mocker.patch(
        "docker.DockerClient.services", return_value=services_model.ServiceCollection()
    )
    mocker.patch("docker.DockerClient.services.list", side_effect=docker_services)
    mocker.patch("docker.models.networks.NetworkCollection.list", return_value=[])
    mocker.patch("docker.models.configs.ConfigCollection.list", return_value=[])

    docker_service_remove = mocker.patch(
        "docker.models.services.Service.remove", return_value=None
    )

    lite_local_runtime.LiteLocalRuntime(
        scan_id="1",
        bus_url="bus",
        bus_vhost="/",
        bus_management_url="mgmt",
        bus_exchange_topic="topic",
        network="privnet",
        redis_url="redis://redis",
        tracing_collector_url="jaeger://localhost/",
    ).stop(scan_id="9999")

    docker_service_remove.assert_not_called()


def testLiteLocalCreateAgentService_whenAgentDefAndAgentSettingsAreNotEmpty_serviceCreatedwithAgentSettings(
    mocker,
):
    """Test creation of the agent service : Case where agent definitions & agent settings have different values for
    some attributes, the agent settings values should override.
    """
    agent_def = agent_definitions.AgentDefinition(
        name="agent_name_from_def",
        mounts=["def_mount1", "def_mount2"],
        mem_limit=420000,
        service_name="my_service",
        restart_policy="any",
    )
    mocker.patch(
        "ostorlab.runtimes.lite_local.agent_runtime.AgentRuntime.create_agent_definition_from_label",
        return_value=agent_def,
    )
    mocker.patch.object(
        ostorlab.runtimes.definitions.AgentSettings,
        "container_image",
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
        bus_url="bus",
        bus_vhost="/",
        bus_management_url="mgmt",
        bus_exchange_topic="topic",
        redis_url="redis://redis",
        tracing_collector_url="jaeger://localhost/",
    )
    runtime_agent.create_agent_service(network_name="test", extra_configs=[])

    kwargs = create_service_mock.call_args.kwargs
    # assert arguments were overridden by the agent settings.
    assert kwargs["resources"]["Limits"]["MemoryBytes"] == 700000
    assert kwargs["mounts"] == ["settings_mount1"]
    assert kwargs["restart_policy"]["Condition"] == "on-failure"
    assert kwargs["name"] == "my_service"
