"""Unittest for local runtime."""

from typing import Any

import docker
import pytest
from docker.models import services as services_model
from pytest_mock import plugin

import ostorlab
from ostorlab import exceptions
from ostorlab.assets import android_apk
from ostorlab.runtimes import definitions
from ostorlab.runtimes.local import runtime as local_runtime
from ostorlab.runtimes.local.models import models


@pytest.mark.skip(reason="Missing inject asset agent.")
@pytest.mark.docker
def testRuntimeScan_whenEmptyRunDefinition_runtimeServicesAreRunning():
    local_runtime_instance = local_runtime.LocalRuntime()
    asset = android_apk.AndroidApk(content=b"APK")
    agent_group_definition = definitions.AgentGroupDefinition(agents=[])

    local_runtime_instance.scan(
        title="test local",
        agent_group_definition=agent_group_definition,
        assets=[asset],
    )

    docker_client = docker.from_env()

    services = docker_client.services.list(
        filters={"label": f"ostorlab.universe={local_runtime_instance.name}"}
    )
    assert any(s.name.startswith("mq_") for s in services)


@pytest.mark.skip(reason="Missing sample agents to test with.")
@pytest.mark.docker
def testRuntimeScan_whenValidAgentRunDefinitionAndAssetAreProvided_scanIsRunning():
    local_runtime_instance = local_runtime.LocalRuntime()
    asset = android_apk.AndroidApk(content=b"APK")
    agent_group_definition = definitions.AgentGroupDefinition(agents=[])

    local_runtime_instance.scan(
        title="test local",
        agent_group_definition=agent_group_definition,
        assets=[asset],
    )

    docker_client = docker.from_env()

    services = docker_client.services.list(
        filters={"label": f"ostorlab.universe={local_runtime_instance.name}"}
    )
    assert any(s.name.startswith("mq_") for s in services)
    assert any(s.name.starts_with("agent_") for s in services)
    # TODO(alaeddine): check for asset injection.
    configs = docker_client.configs.list()
    assert any(c.name.starts_with("agent_") for c in configs)


@pytest.mark.docker
def testRuntimeScanStop_whenScanIdIsValid_RemovesScanService(mocker, db_engine_path):
    """Unittest for the scan stop method when there are local scans available.
    Gets the docker services and checks for those with ostorlab.universe
    as one of the labels to find the service with the given scan id.
    Removes the scan service matching the provided id.
    """
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    create_scan_db = models.Scan.create("test")

    def docker_services():
        """Method for mocking the services list response."""
        with models.Database() as session:
            scan = session.query(models.Scan).first()
        services = [
            {
                "ID": "0099i5n1y3gycuekvksyqyxav",
                "CreatedAt": "2021-12-27T13:37:02.795789947Z",
                "Spec": {"Labels": {"ostorlab.universe": scan.id}},
            },
            {
                "ID": "0099i5n1y3gycuekvksyqyxav",
                "CreatedAt": "2021-12-27T13:37:02.795789947Z",
                "Spec": {"Labels": {"ostorlab.universe": 9999}},
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
    local_runtime.LocalRuntime().stop(scan_id=create_scan_db.id)

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
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    create_scan_db = models.Scan.create("test")
    local_runtime.LocalRuntime().stop(scan_id=create_scan_db.id)

    local_runtime.LocalRuntime().stop(scan_id="9999")

    docker_service_remove.assert_not_called()


def testRuntimeScanList_whenScansArePresent_showsScans(mocker, db_engine_path):
    """Unittest for the scan list method when there are local scans available.
    Gets the docker services and checks for those with ostorlab.universe
    as one of the labels.
    Shows the list of scans.
    """

    def docker_services():
        """Method for mocking the scan list response."""
        services = [
            {
                "ID": "0099i5n1y3gycuekvksyqyxav",
                "CreatedAt": "2021-12-27T13:37:02.795789947Z",
                "Spec": {"Labels": {"ostorlab.universe": "1"}},
            },
            {
                "ID": "0099i5n1y3gycuekvksyqyxav",
                "CreatedAt": "2021-12-27T13:37:02.795789947Z",
                "Spec": {"Labels": {"ostorlab.mq": ""}},
            },
        ]

        return [services_model.Service(attrs=service) for service in services]

    mocker.patch.object(
        ostorlab.runtimes.local.models.models, "ENGINE_URL", db_engine_path
    )
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch(
        "docker.DockerClient.services", return_value=services_model.ServiceCollection()
    )
    mocker.patch("docker.DockerClient.services.list", side_effect=docker_services)

    scans = local_runtime.LocalRuntime().list()

    assert len(scans) == 0


@pytest.mark.docker
def testScanInLocalRuntime_whenFlagToDisableDefaultAgentsIsPassed_shouldNotStartTrackerAndPersistVulnAgents(
    mocker: plugin.MockerFixture, local_runtime_mocks: Any
) -> None:
    """Ensure the tracker & local persist vulnz agents do not get started,
    when the flag to disable them is passed to the local runtime instance.
    """
    mocker.patch(
        "ostorlab.runtimes.definitions.AgentSettings.container_image",
        return_value="agent_42_docker_image",
        new_callable=mocker.PropertyMock,
    )
    agent_runtime_mock = mocker.patch(
        "ostorlab.runtimes.local.agent_runtime.AgentRuntime"
    )
    local_runtime_instance = local_runtime.LocalRuntime(run_default_agents=False)
    agent_group_definition = definitions.AgentGroupDefinition(
        agents=[definitions.AgentSettings(key="agent/ostorlab/agent42")]
    )

    local_runtime_instance.can_run(agent_group_definition=agent_group_definition)
    local_runtime_instance.scan(
        title="test local",
        agent_group_definition=agent_group_definition,
        assets=[android_apk.AndroidApk(content=b"APK")],
    )

    start_agent_mock_call_args = agent_runtime_mock.call_args_list
    assert (
        start_agent_mock_call_args[0].kwargs["agent_settings"].key
        == "agent/ostorlab/agent42"
    )
    assert (
        start_agent_mock_call_args[1].kwargs["agent_settings"].key
        == "agent/ostorlab/inject_asset"
    )
    assert (
        all(
            call_arg.kwargs["agent_settings"].key
            != "agent/ostorlab/local_persist_vulnz"
            for call_arg in start_agent_mock_call_args
        )
        is True
    )
    assert (
        all(
            call_arg.kwargs["agent_settings"].key != "agent/ostorlab/tracker"
            for call_arg in start_agent_mock_call_args
        )
        is True
    )


@pytest.mark.docker
def testScanInLocalRuntime_whenScanIdIsPassed_shouldUseTheScanIdAsUniverseLabelInsteadOfIdInLocalDb(
    mocker: plugin.MockerFixture, local_runtime_mocks: Any
) -> None:
    """Ensure if a scan_id is passed as argument to the Local runtime,
    it should be used to set the universe label for the created docker services,
    over the scan_id created in the local database."""
    mocker.patch(
        "ostorlab.runtimes.definitions.AgentSettings.container_image",
        return_value="agent_42_docker_image",
        new_callable=mocker.PropertyMock,
    )
    agent_runtime_mock = mocker.patch(
        "ostorlab.runtimes.local.agent_runtime.AgentRuntime"
    )
    local_runtime_instance = local_runtime.LocalRuntime(scan_id=42)
    agent_group_definition = definitions.AgentGroupDefinition(
        agents=[definitions.AgentSettings(key="agent/ostorlab/agent42")]
    )

    local_runtime_instance.can_run(agent_group_definition=agent_group_definition)
    local_runtime_instance.scan(
        title="test local",
        agent_group_definition=agent_group_definition,
        assets=[android_apk.AndroidApk(content=b"APK")],
    )

    start_agent_mock_call_args = agent_runtime_mock.call_args_list
    assert (
        all(
            mock_call.kwargs["runtime_name"] == 42
            for mock_call in start_agent_mock_call_args
        )
        is True
    )
    with models.Database() as session:
        assert session.query(models.Scan).count() == 1
        scan = session.query(models.Scan).first()
        assert scan.id != 42


@pytest.mark.docker
def testRuntime_WhenCantInitSwarm_shouldShowUserFriendlyMessage(
    mocker: plugin.MockerFixture,
    httpx_mock,
) -> None:
    """Ensure the runtime retries to init swarm if it fails the first time."""
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_docker_working", return_value=True
    )
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_user_permitted", return_value=True
    )
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_sys_arch_supported",
        return_value=True,
    )
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_swarm_initialized",
        return_value=False,
    )
    mocker.patch("time.sleep")
    httpx_mock.get(
        "http+docker://localhost/version", [{"json": {"ApiVersion": "1.35"}}]
    )
    httpx_mock.get("http+docker://localhost/v1.35/swarm", json={"ID": "1234"})
    mock_swarm_init = httpx_mock.add_response(
        method="POST", url="http+docker://localhost/v1.35/swarm/init", status_code=400
    )
    local_runtime_instance = local_runtime.LocalRuntime(run_default_agents=False)

    with pytest.raises(exceptions.OstorlabError):
        local_runtime_instance.can_run(
            agent_group_definition=definitions.AgentGroupDefinition(agents=[])
        )

    assert mock_swarm_init.call_count == 3


def testRuntimeScanList_whenDockerIsDown_DoesNotCrash(
    mocker: plugin.MockerFixture,
) -> None:
    """Unit test for the scan list method when docker throws an exception, its handled and doesn't crash."""

    mocker.patch("docker.from_env", side_effect=docker.errors.DockerException)

    scans = local_runtime.LocalRuntime().list()

    assert scans is None
