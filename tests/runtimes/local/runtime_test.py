"""Unittest for local runtime."""

import base64
import datetime
from typing import Any
from unittest import mock

import docker
import pytest
import requests
from docker.models import networks as networks_model
from docker.models import services as services_model
from pytest_mock import plugin

import ostorlab
from ostorlab import exceptions
from ostorlab.assets import android_apk
from ostorlab.assets import ipv4
from ostorlab.runtimes import definitions
from ostorlab.runtimes.local import runtime as local_runtime
from ostorlab.runtimes.local import snapshot_storage
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
    mocker.patch("docker.models.volumes.VolumeCollection.list", return_value=[])

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

    docker_service_remove.assert_not_called()


@pytest.mark.docker
def testRuntimeScanStop_whenMatchingVolumeExists_removesOnlyScanVolume(
    mocker, db_engine_path
):
    """Stopping a scan should remove only volumes labeled for that scan."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    create_scan_db = models.Scan.create("test")

    matching_volume = mocker.MagicMock(
        name="matching_volume",
        attrs={"Labels": {"ostorlab.universe": str(create_scan_db.id)}},
    )
    other_volume = mocker.MagicMock(
        name="other_volume",
        attrs={"Labels": {"ostorlab.universe": "9999"}},
    )
    mocker.patch(
        "docker.DockerClient.services", return_value=services_model.ServiceCollection()
    )
    mocker.patch("docker.DockerClient.services.list", return_value=[])
    mocker.patch("docker.models.networks.NetworkCollection.list", return_value=[])
    mocker.patch("docker.models.configs.ConfigCollection.list", return_value=[])
    mocker.patch(
        "docker.models.volumes.VolumeCollection.list",
        return_value=[matching_volume, other_volume],
    )

    local_runtime.LocalRuntime().stop(scan_id=create_scan_db.id)

    matching_volume.remove.assert_called_once_with(force=True)
    other_volume.remove.assert_not_called()


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
    mock_client = mocker.Mock()
    mock_client.services.list.side_effect = docker_services
    mocker.patch("docker.from_env", return_value=mock_client)

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
    mock_docker = mocker.MagicMock()
    mock_docker.swarm.init.side_effect = docker.errors.DockerException("error")
    mocker.patch("docker.from_env", return_value=mock_docker)

    local_runtime_instance = local_runtime.LocalRuntime(run_default_agents=False)

    with pytest.raises(exceptions.OstorlabError):
        local_runtime_instance.can_run(
            agent_group_definition=definitions.AgentGroupDefinition(agents=[])
        )


def testRuntimeScanList_whenDockerIsDown_DoesNotCrash(
    mocker: plugin.MockerFixture,
) -> None:
    """Unit test for the scan list method when docker throws an exception, its handled and doesn't crash."""

    mocker.patch("docker.from_env", side_effect=docker.errors.DockerException)

    scans = local_runtime.LocalRuntime().list()

    assert scans is None


def testRuntimeScanList_whenStateIsProvided_filtersScansByState(mocker, db_engine_path):
    """Unittest for the scan list method with state filter.
    Should return only scans matching the provided state.
    """
    mocker.patch.object(
        ostorlab.runtimes.local.models.models, "ENGINE_URL", db_engine_path
    )
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mock_client = mocker.Mock()
    mock_client.services.list.return_value = []
    mocker.patch("docker.from_env", return_value=mock_client)

    models.Scan.create(title="scan1", progress=models.ScanProgress.IN_PROGRESS)
    models.Scan.create(title="scan2", progress=models.ScanProgress.DONE)
    models.Scan.create(title="scan3", progress=models.ScanProgress.ERROR)

    done_scans = local_runtime.LocalRuntime().list(state="done")
    in_progress_scans = local_runtime.LocalRuntime().list(state="in_progress")
    all_scans = local_runtime.LocalRuntime().list()

    assert len(done_scans) == 1
    assert done_scans[0].progress == "done"
    assert len(in_progress_scans) == 1
    assert in_progress_scans[0].progress == "in_progress"
    assert len(all_scans) == 3


@pytest.mark.docker
def testRuntimeScanStop_whenUnrelatedNetworks_removesScanServiceWithoutCrash(
    mocker: plugin.MockerFixture, db_engine_path: str
):
    """Unittest for the scan stop method when there are networks not related to the scan, the process shouldn't crash"""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    create_scan_db = models.Scan.create("test")

    def docker_services() -> list[services_model.Service]:
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

    def docker_networks() -> list[networks_model.Network]:
        """Method for mocking the services list response."""
        with models.Database() as session:
            scan = session.query(models.Scan).first()
        networks = [
            {
                "ID": "0099i5n1y3gycuekvksyqyxav",
                "CreatedAt": "2021-12-27T13:37:02.795789947Z",
                "Labels": {},
            },
            {
                "ID": "0099i5n1y3gycuekvksyqyxav",
                "CreatedAt": "2021-12-27T13:37:02.795789947Z",
                "Labels": {"ostorlab.universe": scan.id},
            },
        ]

        return [networks_model.Network(attrs=network) for network in networks]

    mocker.patch(
        "docker.DockerClient.services", return_value=services_model.ServiceCollection()
    )
    mocker.patch("docker.DockerClient.services.list", side_effect=docker_services)
    mocker.patch(
        "docker.models.networks.NetworkCollection.list", return_value=docker_networks()
    )
    mocker.patch("docker.models.configs.ConfigCollection.list", return_value=[])
    docker_network_remove = mocker.patch("docker.models.networks.Network.remove")
    docker_service_remove = mocker.patch(
        "docker.models.services.Service.remove", return_value=None
    )

    local_runtime.LocalRuntime().stop(scan_id=create_scan_db.id)

    docker_service_remove.assert_called_once()
    docker_network_remove.assert_called_once()


def testLocalRuntimeInit_always_setsMaxPoolSize(mocker):
    """Test LocalRuntime initializes docker client with increased pool size."""
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_docker_working", return_value=True
    )
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_sys_arch_supported",
        return_value=True,
    )
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_user_permitted", return_value=True
    )
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_swarm_initialized",
        return_value=True,
    )
    mock_from_env = mocker.patch("docker.from_env")

    runtime = local_runtime.LocalRuntime()
    runtime._docker_checks()
    mock_from_env.assert_any_call(max_pool_size=100)


def testLocalRuntimeScan_whenAssetsProvidedAndAgentMissing_usesDefaultSettings(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Test that scan calls _inject_assets with None when assets are provided but cloud_inject_asset is missing."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_docker_installed",
        return_value=True,
    )
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_sys_arch_supported",
        return_value=True,
    )
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_user_permitted", return_value=True
    )
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_docker_working", return_value=True
    )
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_swarm_initialized",
        return_value=True,
    )
    mocker.patch("docker.from_env", return_value=mocker.Mock())

    runtime = local_runtime.LocalRuntime()

    agent_group = definitions.AgentGroupDefinition(agents=[])
    assets = [ipv4.IPv4(host="8.8.8.8", mask="32")]

    mocker.patch.object(runtime, "_start_agents")
    mocker.patch.object(runtime, "_check_agents_healthy", return_value=True)
    mocker.patch.object(runtime, "_check_services_healthy")
    mocker.patch.object(runtime, "_start_services")
    mocker.patch.object(runtime, "_create_network")
    mocker.patch.object(runtime, "_start_pre_agents")
    mocker.patch.object(runtime, "_start_post_agents")
    mocker.patch.object(runtime, "_update_scan_progress")
    mocker.patch.object(runtime, "_wait_log_streamer")

    mock_inject = mocker.patch.object(runtime, "_inject_assets")

    runtime.scan(title="test", agent_group_definition=agent_group, assets=assets)

    mock_inject.assert_called_once()
    _, kwargs = mock_inject.call_args
    assert kwargs["agent_settings"] is None


def testLocalRuntimeScan_whenAssetsProvidedAndAgentPresent_callsInjectAssets(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Test that scan calls _inject_assets when assets and cloud_inject_asset are provided."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_docker_installed",
        return_value=True,
    )
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_sys_arch_supported",
        return_value=True,
    )
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_user_permitted", return_value=True
    )
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_docker_working", return_value=True
    )
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_swarm_initialized",
        return_value=True,
    )
    mocker.patch("docker.from_env", return_value=mocker.Mock())

    runtime = local_runtime.LocalRuntime()

    agent_settings = definitions.AgentSettings(key="agent/ostorlab/cloud_inject_asset")
    agent_group = definitions.AgentGroupDefinition(agents=[agent_settings])
    assets = [ipv4.IPv4(host="8.8.8.8", mask="32")]

    mocker.patch.object(runtime, "_start_agents")
    mocker.patch.object(runtime, "_check_agents_healthy", return_value=True)
    mocker.patch.object(runtime, "_check_services_healthy")
    mocker.patch.object(runtime, "_start_services")
    mocker.patch.object(runtime, "_create_network")
    mocker.patch.object(runtime, "_start_pre_agents")
    mocker.patch.object(runtime, "_start_post_agents")
    mocker.patch.object(runtime, "_update_scan_progress")
    mocker.patch.object(runtime, "_wait_log_streamer")

    mock_inject = mocker.patch.object(runtime, "_inject_assets")

    runtime.scan(title="test", agent_group_definition=agent_group, assets=assets)

    mock_inject.assert_called_once_with(assets=assets, agent_settings=agent_settings)


def testLocalRuntimeInjectAssets_always_createsVolumeAndStartsAgent(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Test that _inject_assets creates a volume and starts the agent."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_docker_installed",
        return_value=True,
    )
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_sys_arch_supported",
        return_value=True,
    )
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_user_permitted", return_value=True
    )
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_docker_working", return_value=True
    )
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_swarm_initialized",
        return_value=True,
    )
    mocker.patch("docker.from_env", return_value=mocker.Mock())

    runtime = local_runtime.LocalRuntime()
    runtime._scan_db = models.Scan.create("test")

    agent_settings = definitions.AgentSettings(key="agent/ostorlab/cloud_inject_asset")
    assets = [ipv4.IPv4(host="8.8.8.8", mask="32")]

    mock_create_volume = mocker.patch("ostorlab.utils.volumes.create_volume")
    mock_start_agent = mocker.patch.object(runtime, "_start_agent", return_value=None)

    runtime._inject_assets(assets=assets, agent_settings=agent_settings)

    mock_create_volume.assert_called_once()
    mock_start_agent.assert_called_once()
    _args, kwargs = mock_start_agent.call_args
    assert kwargs["agent"].key == agent_settings.key
    assert any(m["Target"] == "/asset" for m in kwargs["extra_mounts"])


def testLocalRuntimeInjectAssets_whenAgentSettingsNone_usesDefaultSettings(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Test that _inject_assets uses default settings when agent_settings is None."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_docker_installed",
        return_value=True,
    )
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_sys_arch_supported",
        return_value=True,
    )
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_user_permitted", return_value=True
    )
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_docker_working", return_value=True
    )
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_swarm_initialized",
        return_value=True,
    )
    mocker.patch("docker.from_env", return_value=mocker.Mock())

    runtime = local_runtime.LocalRuntime()
    runtime._scan_db = models.Scan.create("test")

    assets = [ipv4.IPv4(host="8.8.8.8", mask="32")]

    mock_create_volume = mocker.patch("ostorlab.utils.volumes.create_volume")
    mock_start_agent = mocker.patch.object(runtime, "_start_agent", return_value=None)

    runtime._inject_assets(assets=assets, agent_settings=None)

    mock_create_volume.assert_called_once()
    mock_start_agent.assert_called_once()
    _args, kwargs = mock_start_agent.call_args
    assert kwargs["agent"].key == "agent/ostorlab/inject_asset"


@pytest.fixture
def docker_client(mocker: plugin.MockerFixture) -> mock.MagicMock:
    client = mocker.MagicMock()
    mocker.patch("docker.from_env", return_value=client)
    return client


@pytest.fixture
def restore_service(docker_client: mock.MagicMock) -> mock.MagicMock:
    """The run-once restore service, its task completes unless a test changes it."""
    service = docker_client.services.create.return_value
    service.tasks.return_value = [{"Status": {"State": "complete"}}]
    service.logs.return_value = [b"restore ", b"failed"]
    return service


@pytest.fixture
def snapshot_runtime(
    mocker: plugin.MockerFixture,
    db_engine_path: str,
    docker_client: mock.MagicMock,
) -> local_runtime.LocalRuntime:
    """A local runtime of scan 42 whose services run, ready to restore a snapshot."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    mocker.patch(
        "ostorlab.runtimes.definitions.AgentSettings.container_image",
        return_value="stop_scan_image",
        new_callable=mocker.PropertyMock,
    )
    mocker.patch("ostorlab.runtimes.local.runtime.volumes.create_volume")
    runtime = local_runtime.LocalRuntime(scan_id="42", run_default_agents=False)
    runtime._docker_client = docker_client
    runtime._mq_service = mocker.Mock(url="amqp://guest:guest@mq_42:5672/")
    runtime._redis_service = mocker.Mock(url="redis://redis_42:6379/")
    return runtime


SNAPSHOT_AGENT_GROUP = definitions.AgentGroupDefinition(
    agents=[definitions.AgentSettings(key="agent/ostorlab/stop_scan")]
)


def testRestoreSnapshot_always_runsTheRestoreOnceFromTheReadOnlySnapshotVolume(
    snapshot_runtime: local_runtime.LocalRuntime,
    docker_client: mock.MagicMock,
    restore_service: mock.MagicMock,
) -> None:
    snapshot_runtime._restore_snapshot(b"snapshot", SNAPSHOT_AGENT_GROUP)

    local_runtime.volumes.create_volume.assert_called_once_with(
        "snapshot_42",
        {"snapshot.pb.gz": b"snapshot"},
        labels={"ostorlab.universe": "42"},
    )
    restore_kwargs = docker_client.services.create.call_args.kwargs
    assert restore_kwargs["image"] == "stop_scan_image"
    assert restore_kwargs["command"] == [
        "python3",
        "-m",
        "ostorlab.runtimes.local.snapshot_state",
        "restore",
        "--mq-url",
        "amqp://guest:guest@mq_42:5672/",
        "--redis-url",
        "redis://redis_42:6379/",
    ]
    assert restore_kwargs["networks"] == ["ostorlab_local_network_42"]
    # Run once: restarting a partial restore would publish its messages twice.
    assert restore_kwargs["restart_policy"]["Condition"] == "none"
    [mount] = restore_kwargs["mounts"]
    assert mount["Source"] == "snapshot_42"
    assert mount["Target"] == "/snapshot"
    assert mount["ReadOnly"] is True
    restore_service.remove.assert_called_once()
    docker_client.volumes.get.assert_called_with("snapshot_42")
    docker_client.volumes.get.return_value.remove.assert_called_once()


def testRestoreSnapshot_whenTaskFails_raisesWithItsStateErrorExitCodeAndLogs(
    snapshot_runtime: local_runtime.LocalRuntime,
    restore_service: mock.MagicMock,
) -> None:
    restore_service.tasks.return_value = [
        {
            "Status": {
                "State": "rejected",
                "Err": "No such image: stop_scan_image",
                "ContainerStatus": {"ExitCode": 1},
            }
        }
    ]

    with pytest.raises(local_runtime.SnapshotRestoreError) as error:
        snapshot_runtime._restore_snapshot(b"snapshot", SNAPSHOT_AGENT_GROUP)

    message = str(error.value)
    assert "state rejected" in message
    assert "exit code 1" in message
    assert "No such image: stop_scan_image" in message
    assert "restore failed" in message


def testRestoreSnapshot_whenTaskNeverFinishes_raisesTimeoutAndRemovesTheSnapshotVolume(
    mocker: plugin.MockerFixture,
    snapshot_runtime: local_runtime.LocalRuntime,
    docker_client: mock.MagicMock,
    restore_service: mock.MagicMock,
) -> None:
    mocker.patch.object(
        local_runtime, "SNAPSHOT_RESTORE_TIMEOUT", datetime.timedelta(seconds=0)
    )
    restore_service.tasks.return_value = [{"Status": {"State": "running"}}]

    with pytest.raises(local_runtime.SnapshotRestoreError, match="did not finish"):
        snapshot_runtime._restore_snapshot(b"snapshot", SNAPSHOT_AGENT_GROUP)

    restore_service.remove.assert_called_once()
    docker_client.volumes.get.return_value.remove.assert_called_once()


@pytest.mark.parametrize(
    "error",
    [docker.errors.APIError("daemon busy"), requests.ConnectionError("daemon down")],
)
def testRestoreSnapshot_whenLogsCannotBeRead_stillRaisesTheRestoreError(
    snapshot_runtime: local_runtime.LocalRuntime,
    restore_service: mock.MagicMock,
    error: Exception,
) -> None:
    restore_service.tasks.return_value = [{"Status": {"State": "failed"}}]
    restore_service.logs.side_effect = error

    with pytest.raises(local_runtime.SnapshotRestoreError, match="state failed"):
        snapshot_runtime._restore_snapshot(b"snapshot", SNAPSHOT_AGENT_GROUP)


@pytest.mark.parametrize(
    "error",
    [docker.errors.APIError("swarm busy"), requests.ReadTimeout("daemon slow")],
)
def testRestoreSnapshot_whenRestoreServiceCannotBeRemoved_raisesRestoreErrorAndRemovesVolume(
    snapshot_runtime: local_runtime.LocalRuntime,
    docker_client: mock.MagicMock,
    restore_service: mock.MagicMock,
    error: Exception,
) -> None:
    """A failed cleanup of the restore service neither hides the restore error nor leaves the snapshot."""
    restore_service.tasks.return_value = [{"Status": {"State": "failed"}}]
    restore_service.remove.side_effect = error

    with pytest.raises(local_runtime.SnapshotRestoreError):
        snapshot_runtime._restore_snapshot(b"snapshot", SNAPSHOT_AGENT_GROUP)

    restore_service.remove.assert_called_once()
    docker_client.volumes.get.return_value.remove.assert_called_once()


def testRestoreSnapshot_whenRestoreServiceCannotBeCreated_raisesRestoreErrorAndRemovesTheSnapshotVolume(
    snapshot_runtime: local_runtime.LocalRuntime,
    docker_client: mock.MagicMock,
) -> None:
    docker_client.services.create.side_effect = docker.errors.APIError("no node")

    with pytest.raises(local_runtime.SnapshotRestoreError, match="could not start"):
        snapshot_runtime._restore_snapshot(b"snapshot", SNAPSHOT_AGENT_GROUP)

    docker_client.volumes.get.assert_called_with("snapshot_42")
    docker_client.volumes.get.return_value.remove.assert_called_once()


def testRestoreSnapshot_whenAgentGroupHasNoSnapshotAgent_raisesSnapshotRestoreError(
    snapshot_runtime: local_runtime.LocalRuntime,
    docker_client: mock.MagicMock,
) -> None:
    agent_group_definition = definitions.AgentGroupDefinition(
        agents=[definitions.AgentSettings(key="agent/ostorlab/agent42")]
    )

    with pytest.raises(local_runtime.SnapshotRestoreError):
        snapshot_runtime._restore_snapshot(b"snapshot", agent_group_definition)

    docker_client.services.create.assert_not_called()


def testScanInLocalRuntime_whenScanSnapshotIsPassed_restoresBeforeTheAgentsAndSkipsAssetInjection(
    mocker: plugin.MockerFixture, snapshot_runtime: local_runtime.LocalRuntime
) -> None:
    calls = mocker.Mock()
    for name in [
        "_create_network",
        "_remove_leftover_mq_volume",
        "_start_services",
        "_check_services_healthy",
        "_restore_snapshot",
        "_start_agents",
        "_inject_assets",
        "_update_scan_progress",
        "_wait_log_streamer",
    ]:
        mocker.patch.object(snapshot_runtime, name, getattr(calls, name))
    mocker.patch.object(snapshot_runtime, "_check_agents_healthy", return_value=True)

    snapshot_runtime.scan(
        title="test local",
        agent_group_definition=SNAPSHOT_AGENT_GROUP,
        assets=[android_apk.AndroidApk(content=b"APK")],
        scan_snapshot=b"snapshot",
    )

    call_names = [call[0] for call in calls.mock_calls]
    assert call_names.index("_remove_leftover_mq_volume") < call_names.index(
        "_start_services"
    )
    assert call_names.index("_check_services_healthy") < call_names.index(
        "_restore_snapshot"
    )
    assert call_names.index("_restore_snapshot") < call_names.index("_start_agents")
    assert "_inject_assets" not in call_names
    calls._restore_snapshot.assert_called_once_with(b"snapshot", SNAPSHOT_AGENT_GROUP)


def testRemoveLeftoverMqVolume_whenVolumeIsLeftOver_removesIt(
    snapshot_runtime: local_runtime.LocalRuntime, docker_client: mock.MagicMock
) -> None:
    """An earlier restore published its messages to the volume, restoring on top of them would duplicate them."""
    snapshot_runtime._remove_leftover_mq_volume()

    docker_client.volumes.get.assert_called_once_with("42_mq_data")
    docker_client.volumes.get.return_value.remove.assert_called_once()


def testRemoveLeftoverMqVolume_whenNoVolumeIsLeftOver_doesNothing(
    snapshot_runtime: local_runtime.LocalRuntime, docker_client: mock.MagicMock
) -> None:
    docker_client.volumes.get.side_effect = docker.errors.NotFound("no volume")

    snapshot_runtime._remove_leftover_mq_volume()

    docker_client.volumes.get.assert_called_once_with("42_mq_data")


def testRemoveLeftoverMqVolume_whenVolumeCannotBeRemoved_raisesSnapshotRestoreError(
    snapshot_runtime: local_runtime.LocalRuntime, docker_client: mock.MagicMock
) -> None:
    docker_client.volumes.get.return_value.remove.side_effect = docker.errors.APIError(
        "volume in use"
    )

    with pytest.raises(local_runtime.SnapshotRestoreError):
        snapshot_runtime._remove_leftover_mq_volume()


def testAgentExtraEnv_whenScannerHasSnapshotStorage_givesItToTheStopScanAgentOnly(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Only the stop scan agent uploads snapshots, the service account key is not given to other agents."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    runtime = local_runtime.LocalRuntime(
        scan_id="42",
        run_default_agents=False,
        snapshot_storage_settings=snapshot_storage.SnapshotStorageSettings(
            bucket_path="gs://scan-snapshots/scan_snapshots",
            service_account_key='{"type": "service_account"}',
        ),
    )

    stop_scan_env = runtime._agent_extra_env(
        definitions.AgentSettings(key="agent/ostorlab/stop_scan")
    )
    nmap_env = runtime._agent_extra_env(
        definitions.AgentSettings(key="agent/ostorlab/nmap")
    )

    assert stop_scan_env == {
        "OSTORLAB_SNAPSHOT_BUCKET": "gs://scan-snapshots/scan_snapshots",
        "OSTORLAB_SNAPSHOT_SERVICE_ACCOUNT": base64.b64encode(
            b'{"type": "service_account"}'
        ).decode(),
    }
    assert nmap_env == {}


def testLocalRuntimeScan_always_checksServicesHealthyBeforeStartingAgents(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Agents must only start once the MQ and other core services are ready."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_docker_installed",
        return_value=True,
    )
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_sys_arch_supported",
        return_value=True,
    )
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_user_permitted", return_value=True
    )
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_docker_working", return_value=True
    )
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_swarm_initialized",
        return_value=True,
    )
    mocker.patch("docker.from_env", return_value=mocker.Mock())
    runtime = local_runtime.LocalRuntime()
    calls = mocker.Mock()
    for name in [
        "_create_network",
        "_start_services",
        "_check_services_healthy",
        "_start_pre_agents",
        "_start_agents",
        "_start_post_agents",
        "_update_scan_progress",
        "_wait_log_streamer",
    ]:
        mocker.patch.object(runtime, name, getattr(calls, name))
    mocker.patch.object(runtime, "_check_agents_healthy", return_value=True)

    runtime.scan(
        title="test",
        agent_group_definition=definitions.AgentGroupDefinition(agents=[]),
        assets=None,
    )

    call_names = [call[0] for call in calls.mock_calls]
    assert call_names.index("_check_services_healthy") < call_names.index(
        "_start_pre_agents"
    )
    assert call_names.index("_check_services_healthy") < call_names.index(
        "_start_agents"
    )


def testRestoreSnapshot_whenSnapshotVolumeCannotBeWritten_raisesSnapshotRestoreError(
    snapshot_runtime: local_runtime.LocalRuntime,
    docker_client: mock.MagicMock,
) -> None:
    local_runtime.volumes.create_volume.side_effect = requests.ConnectionError(
        "daemon down"
    )

    with pytest.raises(local_runtime.SnapshotRestoreError, match="could not start"):
        snapshot_runtime._restore_snapshot(b"snapshot", SNAPSHOT_AGENT_GROUP)

    docker_client.services.create.assert_not_called()


def testRestoreSnapshot_whenSnapshotAgentImageCannotBeLookedUp_raisesSnapshotRestoreError(
    mocker: plugin.MockerFixture,
    snapshot_runtime: local_runtime.LocalRuntime,
    docker_client: mock.MagicMock,
) -> None:
    """Resolving the image of the snapshot agent talks to the docker daemon, which may be down."""
    mocker.patch(
        "ostorlab.runtimes.definitions.AgentSettings.container_image",
        side_effect=docker.errors.DockerException("daemon down"),
        new_callable=mocker.PropertyMock,
    )

    with pytest.raises(
        local_runtime.SnapshotRestoreError, match="could not be looked up"
    ):
        snapshot_runtime._restore_snapshot(b"snapshot", SNAPSHOT_AGENT_GROUP)

    docker_client.services.create.assert_not_called()
    local_runtime.volumes.create_volume.assert_not_called()
