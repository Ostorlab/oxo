"""Unittest for local runtime."""

import typing
from typing import Any

import docker
import pytest
import tenacity
from docker.models import networks as networks_model
from docker.models import services as services_model
from pytest_mock import plugin

import ostorlab
from ostorlab import exceptions
from ostorlab.assets import android_apk
from ostorlab.assets import ipv4
from ostorlab.runtimes import definitions
from ostorlab.runtimes.local import agent_runtime
from ostorlab.runtimes.local import runtime as local_runtime
from ostorlab.runtimes.local import scan_state
from ostorlab.runtimes.local import snapshot
from ostorlab.runtimes.local.models import models
from ostorlab.runtimes.local.services import container_exec
from ostorlab.runtimes.local.services import mq


@pytest.mark.skip(reason="Missing inject asset agent.")
@pytest.mark.docker
def testRuntimeScan_whenEmptyRunDefinition_runtimeServicesAreRunning() -> None:
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
def testRuntimeScan_whenValidAgentRunDefinitionAndAssetAreProvided_scanIsRunning() -> (
    None
):
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
    assert any(s.name.startswith("agent_") for s in services)
    # TODO(alaeddine): check for asset injection.
    configs = docker_client.configs.list()
    assert any(c.name.startswith("agent_") for c in configs)


@pytest.mark.docker
def testRuntimeScanStop_whenScanIdIsValid_RemovesScanService(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Unittest for the scan stop method when there are local scans available.
    Gets the docker services and checks for those with ostorlab.universe
    as one of the labels to find the service with the given scan id.
    Removes the scan service matching the provided id.
    """
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    create_scan_db = models.Scan.create("test")

    def docker_services() -> list[services_model.Service]:
        """Method for mocking the services list response."""
        with models.Database() as session:
            scan = session.query(models.Scan).first()
            assert scan is not None
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
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Unittest for the scan stop method when the scan id is invalid.
    Gets the docker services and checks for those with ostorlab.universe
    as one of the labels to find the service with the given scan id.
    Does not remove any service.
    """

    def docker_services() -> list[services_model.Service]:
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
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
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


def testRuntimeScanList_whenScansArePresent_showsScans(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Unittest for the scan list method when there are local scans available.
    Gets the docker services and checks for those with ostorlab.universe
    as one of the labels.
    Shows the list of scans.
    """

    def docker_services() -> list[services_model.Service]:
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
    assert scans is not None

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
        assert scan is not None
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


def testRuntimeScanList_whenStateIsProvided_filtersScansByState(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
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
    assert done_scans is not None
    in_progress_scans = local_runtime.LocalRuntime().list(state="in_progress")
    assert in_progress_scans is not None
    all_scans = local_runtime.LocalRuntime().list()
    assert all_scans is not None

    assert len(done_scans) == 1
    assert done_scans[0].progress == "done"
    assert len(in_progress_scans) == 1
    assert in_progress_scans[0].progress == "in_progress"
    assert len(all_scans) == 3


@pytest.mark.docker
def testRuntimeScanStop_whenUnrelatedNetworks_removesScanServiceWithoutCrash(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Unittest for the scan stop method when there are networks not related to the scan, the process shouldn't crash"""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    create_scan_db = models.Scan.create("test")

    def docker_services() -> list[services_model.Service]:
        """Method for mocking the services list response."""
        with models.Database() as session:
            scan = session.query(models.Scan).first()
            assert scan is not None
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
            assert scan is not None
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


def testLocalRuntimeInit_always_setsMaxPoolSize(mocker: plugin.MockerFixture) -> None:
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


SNAPSHOT_SETTINGS = definitions.SnapshotSettings(
    bucket="scan-snapshots", service_account=b"{}"
)


UNIVERSE_SNAPSHOT = snapshot.UniverseSnapshot(
    exchanges=[{"name": "topic"}],
    queues=[{"name": "nmap"}],
    redis_keys=[snapshot.RedisKey(key=b"k", ttl_ms=0, value=b"v")],
)


def _agent_group() -> definitions.AgentGroupDefinition:
    return definitions.AgentGroupDefinition(
        agents=[
            definitions.AgentSettings(key="agent/ostorlab/nmap"),
            definitions.AgentSettings(key="agent/ostorlab/stop_scan"),
        ]
    )


def testLocalRuntimeScan_whenScanHasSnapshot_restoresBeforeAgentsAndSkipsAssets(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """A paused scan restores its snapshot once the services are ready, before any agent starts, without injecting
    its assets again."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    mocker.patch("docker.from_env", return_value=mocker.Mock())
    runtime = local_runtime.LocalRuntime(snapshot_settings=SNAPSHOT_SETTINGS)
    calls = mocker.Mock()
    for name in [
        "_create_network",
        "_start_services",
        "_check_services_healthy",
        "_restore_snapshot",
        "_start_pre_agents",
        "_start_agents",
        "_start_post_agents",
        "_inject_assets",
        "_update_scan_progress",
        "_wait_log_streamer",
    ]:
        mocker.patch.object(runtime, name, getattr(calls, name))
    mocker.patch.object(runtime, "_load_snapshot", return_value=UNIVERSE_SNAPSHOT)
    mocker.patch.object(runtime, "_check_agents_healthy", return_value=True)

    runtime.scan(
        title="test",
        agent_group_definition=_agent_group(),
        assets=[ipv4.IPv4(host="8.8.8.8", mask="32")],
    )

    call_names = [call[0] for call in calls.mock_calls]
    assert call_names.index("_check_services_healthy") < call_names.index(
        "_restore_snapshot"
    )
    assert call_names.index("_restore_snapshot") < call_names.index("_start_pre_agents")
    assert call_names.index("_restore_snapshot") < call_names.index("_start_agents")
    assert call_names.index("_restore_snapshot") < call_names.index(
        "_start_post_agents"
    )
    assert "_inject_assets" not in call_names
    calls._restore_snapshot.assert_called_once_with(UNIVERSE_SNAPSHOT)


def testLocalRuntimeScan_whenScanHasNoSnapshot_injectsAssetsWithoutRestoring(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """A scan that was never paused injects its assets and restores nothing."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    mocker.patch("docker.from_env", return_value=mocker.Mock())
    runtime = local_runtime.LocalRuntime(snapshot_settings=SNAPSHOT_SETTINGS)
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
        mocker.patch.object(runtime, name)
    mocker.patch.object(runtime, "_load_snapshot", return_value=None)
    mocker.patch.object(runtime, "_check_agents_healthy", return_value=True)
    restore = mocker.patch.object(runtime, "_restore_snapshot")
    inject = mocker.patch.object(runtime, "_inject_assets")

    runtime.scan(
        title="test",
        agent_group_definition=_agent_group(),
        assets=[ipv4.IPv4(host="8.8.8.8", mask="32")],
    )

    restore.assert_not_called()
    inject.assert_called_once()


@pytest.mark.parametrize(
    ("step", "error"),
    [
        ("_load_snapshot", snapshot.StorageError("bucket unreachable")),
        ("_restore_snapshot", local_runtime.SnapshotRestoreError("broken")),
    ],
)
def testLocalRuntimeScan_whenSnapshotFails_raisesAndCleansUp(
    mocker: plugin.MockerFixture,
    db_engine_path: str,
    step: str,
    error: exceptions.OstorlabError,
) -> None:
    """A failed snapshot lookup or restore stops the scan start and removes the universe, no agent starts."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    mocker.patch("docker.from_env", return_value=mocker.Mock())
    runtime = local_runtime.LocalRuntime(snapshot_settings=SNAPSHOT_SETTINGS)
    for name in [
        "_create_network",
        "_start_services",
        "_check_services_healthy",
        "_wait_log_streamer",
    ]:
        mocker.patch.object(runtime, name)
    mocker.patch.object(runtime, "_load_snapshot", return_value=UNIVERSE_SNAPSHOT)
    mocker.patch.object(runtime, "_restore_snapshot")
    mocker.patch.object(runtime, step, side_effect=error)
    start_agents = mocker.patch.object(runtime, "_start_agents")
    update_progress = mocker.patch.object(runtime, "_update_scan_progress")
    cleanup = mocker.patch.object(runtime, "cleanup")

    with pytest.raises(type(error)):
        runtime.scan(title="test", agent_group_definition=_agent_group(), assets=None)

    start_agents.assert_not_called()
    update_progress.assert_called_once_with(models.ScanProgress.ERROR)
    cleanup.assert_called_once()


def testLocalRuntimeLoadSnapshot_always_loadsTheObjectOfTheScan(
    mocker: plugin.MockerFixture,
) -> None:
    """The snapshot of a scan is looked up under its scan id with the runtime storage."""
    load = mocker.patch.object(snapshot, "load", return_value=UNIVERSE_SNAPSHOT)
    runtime = local_runtime.LocalRuntime(
        scan_id="7", snapshot_settings=SNAPSHOT_SETTINGS
    )

    assert runtime._load_snapshot() == UNIVERSE_SNAPSHOT
    load.assert_called_once_with(SNAPSHOT_SETTINGS, "7")


def testLocalRuntimeLoadSnapshot_whenNoSnapshotStorage_returnsNone(
    mocker: plugin.MockerFixture,
) -> None:
    """A scanner without snapshot storage starts every scan from scratch."""
    load = mocker.patch.object(snapshot, "load")
    runtime = local_runtime.LocalRuntime(scan_id="7")

    assert runtime._load_snapshot() is None
    load.assert_not_called()


def testLocalRuntimeLoadSnapshot_whenSnapshotIsInvalid_raisesSnapshotRestoreError(
    mocker: plugin.MockerFixture,
) -> None:
    """A corrupted snapshot keeps the scan paused instead of restarting it from scratch."""
    mocker.patch.object(
        snapshot, "load", side_effect=snapshot.InvalidSnapshotError("corrupted")
    )
    runtime = local_runtime.LocalRuntime(
        scan_id="7", snapshot_settings=SNAPSHOT_SETTINGS
    )

    with pytest.raises(local_runtime.SnapshotRestoreError):
        runtime._load_snapshot()


def testLocalRuntimeLoadSnapshot_whenBucketCannotBeRead_raisesStorageError(
    mocker: plugin.MockerFixture,
) -> None:
    """A bucket that cannot be read is not mistaken for a scan without snapshot."""
    mocker.patch.object(
        snapshot, "load", side_effect=snapshot.StorageError("bucket unreachable")
    )
    runtime = local_runtime.LocalRuntime(
        scan_id="7", snapshot_settings=SNAPSHOT_SETTINGS
    )

    with pytest.raises(snapshot.StorageError):
        runtime._load_snapshot()


def testLocalRuntimeRestoreSnapshot_always_restoresRedisAndMq(
    mocker: plugin.MockerFixture,
) -> None:
    """The snapshot is restored in the universe services."""
    runtime = local_runtime.LocalRuntime(
        scan_id="7", snapshot_settings=SNAPSHOT_SETTINGS
    )
    mq_service = mocker.MagicMock()
    redis_service = mocker.MagicMock()
    runtime._mq_service = mq_service
    runtime._redis_service = redis_service

    runtime._restore_snapshot(UNIVERSE_SNAPSHOT)

    redis_service.restore.assert_called_once_with(UNIVERSE_SNAPSHOT.redis_keys)
    mq_service.restore.assert_called_once_with(
        exchanges=UNIVERSE_SNAPSHOT.exchanges, queues=UNIVERSE_SNAPSHOT.queues
    )


def testLocalRuntimeRestoreSnapshot_whenRestoreFails_raisesSnapshotRestoreError(
    mocker: plugin.MockerFixture,
) -> None:
    """A failed restore in the universe services is reported as a restore error."""
    runtime = local_runtime.LocalRuntime(
        scan_id="7", snapshot_settings=SNAPSHOT_SETTINGS
    )
    runtime._mq_service = mocker.MagicMock()
    redis_service = mocker.MagicMock()
    redis_service.restore.side_effect = container_exec.ExecError("restore failed")
    runtime._redis_service = redis_service

    with pytest.raises(local_runtime.SnapshotRestoreError):
        runtime._restore_snapshot(UNIVERSE_SNAPSHOT)


@pytest.mark.parametrize(
    ("agent_snapshot", "snapshot_settings", "expected_snapshot"),
    [
        (None, SNAPSHOT_SETTINGS, SNAPSHOT_SETTINGS),
        (None, None, None),
        (SNAPSHOT_SETTINGS, None, None),
    ],
)
def testLocalRuntimeStartAgent_always_givesTheRuntimeSnapshotStorageToTheAgent(
    mocker: plugin.MockerFixture,
    agent_snapshot: definitions.SnapshotSettings | None,
    snapshot_settings: definitions.SnapshotSettings | None,
    expected_snapshot: definitions.SnapshotSettings | None,
) -> None:
    """Every agent of the scan receives the snapshot storage of the runtime, an agent never keeps its own."""
    mocker.patch.object(local_runtime, "_has_container_image", return_value=True)
    agent_runtime_class = mocker.patch.object(agent_runtime, "AgentRuntime")
    runtime = local_runtime.LocalRuntime(
        scan_id=42, snapshot_settings=snapshot_settings
    )
    agent = definitions.AgentSettings(
        key="agent/ostorlab/nmap", snapshot=agent_snapshot
    )

    runtime._start_agent(agent)

    assert (
        agent_runtime_class.call_args.kwargs["agent_settings"].snapshot
        == expected_snapshot
    )


SCAN_DEFINITION = scan_state.ScanDefinition(
    agent_group_definition=_agent_group(),
    has_tracker=True,
    timeout=600,
    init_sleep=10,
    follow=["agent/ostorlab/nmap"],
)
CAPTURED_STATE = {
    "exchanges": [{"name": "topic"}],
    "queues": [{"name": "nmap"}],
    "redis_keys": [{"key": "aw==", "ttl_ms": 0, "value": "dg=="}],
}


def _scan_progress(scan_id: int) -> models.ScanProgress | None:
    with models.Database() as session:
        scan = session.query(models.Scan).get(scan_id)
        assert scan is not None
        return typing.cast(models.ScanProgress | None, scan.progress)


def _paused_runtime(
    mocker: plugin.MockerFixture,
) -> tuple[local_runtime.LocalRuntime, Any]:
    """A local runtime whose docker checks pass and whose universe has a MQ service capturing `CAPTURED_STATE`."""
    mocker.patch("docker.from_env", return_value=mocker.MagicMock())
    runtime = local_runtime.LocalRuntime()
    mocker.patch.object(runtime, "_docker_checks")
    mq_service = mocker.MagicMock()
    mq_service.attach.return_value = True
    mq_service.capture.return_value = CAPTURED_STATE
    mocker.patch.object(mq, "LocalRabbitMQ", return_value=mq_service)
    mocker.patch.object(scan_state, "load_definition", return_value=SCAN_DEFINITION)
    return runtime, mq_service


def testLocalRuntimeScan_whenScanIsLocal_savesItsDefinition(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """A local scan keeps its agents and tracker settings, read back to resume it from another oxo process."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    mocker.patch("docker.from_env", return_value=mocker.Mock())
    runtime = local_runtime.LocalRuntime()
    runtime.timeout = 600
    runtime.init_sleep = 10
    runtime.follow = ["agent/ostorlab/nmap"]
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
        mocker.patch.object(runtime, name)
    mocker.patch.object(runtime, "_load_snapshot", return_value=None)
    mocker.patch.object(runtime, "_check_agents_healthy", return_value=True)

    created_scan = runtime.scan(
        title="test", agent_group_definition=_agent_group(), assets=None
    )

    assert created_scan is not None
    assert scan_state.load_definition(created_scan.id) == SCAN_DEFINITION


def testLocalRuntimeScan_whenScanIdIsGiven_doesNotSaveADefinition(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """A scan run for the scanning engine is paused by the stop scan agent, it keeps no local definition."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    mocker.patch("docker.from_env", return_value=mocker.Mock())
    runtime = local_runtime.LocalRuntime(scan_id="se-7")
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
        mocker.patch.object(runtime, name)
    mocker.patch.object(runtime, "_load_snapshot", return_value=None)
    mocker.patch.object(runtime, "_check_agents_healthy", return_value=True)
    save_definition = mocker.patch.object(scan_state, "save_definition")

    runtime.scan(title="test", agent_group_definition=_agent_group(), assets=None)

    save_definition.assert_not_called()


def testLocalRuntimePause_whenScanIsRunning_stopsAgentsSavesSnapshotAndRemovesUniverse(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """The agents stop before the snapshot is taken, the services stop and the universe is removed once it is
    saved."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    scan = models.Scan.create("test", progress=models.ScanProgress.IN_PROGRESS)
    runtime, mq_service = _paused_runtime(mocker)
    calls = mocker.Mock()
    mocker.patch.object(runtime, "_stop_agents", calls._stop_agents)

    def capture(redis_host: str) -> dict[str, Any]:
        calls.capture(redis_host)
        return CAPTURED_STATE

    mq_service.capture.side_effect = capture
    mocker.patch.object(runtime, "_stop_services", calls._stop_services)
    mocker.patch.object(runtime, "cleanup", calls.cleanup)

    runtime.pause(scan_id=scan.id)

    assert [call[0] for call in calls.mock_calls] == [
        "_stop_agents",
        "capture",
        "_stop_services",
        "cleanup",
    ]
    calls.capture.assert_called_once_with(f"redis_{scan.id}")
    calls.cleanup.assert_called_once_with(scan_id=scan.id)
    assert snapshot.load_file(
        scan_state.snapshot_path(scan.id)
    ) == snapshot.from_document(CAPTURED_STATE)
    assert _scan_progress(scan.id) == models.ScanProgress.PAUSED


@pytest.mark.parametrize(
    "progress", [models.ScanProgress.DONE, models.ScanProgress.PAUSED]
)
def testLocalRuntimePause_whenScanIsNotRunning_raisesScanPauseError(
    mocker: plugin.MockerFixture,
    db_engine_path: str,
    progress: models.ScanProgress,
) -> None:
    """Only a running scan can be paused, nothing is stopped."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    scan = models.Scan.create("test", progress=progress)
    runtime, _ = _paused_runtime(mocker)
    stop_agents = mocker.patch.object(runtime, "_stop_agents")

    with pytest.raises(local_runtime.ScanPauseError):
        runtime.pause(scan_id=scan.id)

    stop_agents.assert_not_called()
    assert _scan_progress(scan.id) == progress


def testLocalRuntimePause_whenScanHasNoDefinition_raisesScanPauseError(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """A scan started by an oxo version that kept no definition cannot be resumed, it is not paused."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    scan = models.Scan.create("test", progress=models.ScanProgress.IN_PROGRESS)
    runtime, _ = _paused_runtime(mocker)
    mocker.patch.object(scan_state, "load_definition", return_value=None)
    stop_agents = mocker.patch.object(runtime, "_stop_agents")

    with pytest.raises(local_runtime.ScanPauseError):
        runtime.pause(scan_id=scan.id)

    stop_agents.assert_not_called()


def testLocalRuntimePause_whenCaptureFails_stopsTheScanAndRaisesScanPauseError(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """The agents are stopped, a scan whose snapshot cannot be taken cannot go on, it is stopped."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    scan = models.Scan.create("test", progress=models.ScanProgress.IN_PROGRESS)
    runtime, mq_service = _paused_runtime(mocker)
    mocker.patch.object(runtime, "_stop_agents")
    mq_service.capture.side_effect = container_exec.ExecError("capture failed")
    stop = mocker.patch.object(runtime, "stop")

    with pytest.raises(local_runtime.ScanPauseError):
        runtime.pause(scan_id=scan.id)

    stop.assert_called_once_with(scan_id=scan.id)
    assert scan_state.snapshot_path(scan.id).exists() is False


def testLocalRuntimeStopAgents_always_removesAgentServicesAndWaitsForTheirContainers(
    mocker: plugin.MockerFixture,
) -> None:
    """Only the agent services are removed, the MQ and Redis keep running for the capture."""
    docker_client = mocker.MagicMock()
    mocker.patch("docker.from_env", return_value=docker_client)
    runtime = local_runtime.LocalRuntime(scan_id="7")
    runtime._docker_client = docker_client
    agent_service = mocker.MagicMock()
    agent_service.name = "agent_nmap_7"
    mq_service = mocker.MagicMock()
    mq_service.name = "mq_7"
    docker_client.services.list.return_value = [agent_service, mq_service]
    docker_client.containers.list.return_value = []

    runtime._stop_agents()

    agent_service.remove.assert_called_once()
    mq_service.remove.assert_not_called()
    docker_client.containers.list.assert_called_once_with(
        all=True, filters={"label": "com.docker.swarm.service.name=agent_nmap_7"}
    )


def testLocalRuntimeWaitServicesStopped_whenContainerKeepsRunning_raisesServicesNotStopped(
    mocker: plugin.MockerFixture,
) -> None:
    """The snapshot is not taken while an agent may still consume messages."""
    docker_client = mocker.MagicMock()
    docker_client.containers.list.return_value = [mocker.MagicMock()]
    runtime = local_runtime.LocalRuntime(scan_id="7")
    runtime._docker_client = docker_client
    wait = local_runtime.LocalRuntime._wait_services_stopped.retry_with(  # type: ignore[attr-defined]
        stop=tenacity.stop_after_attempt(1)
    )

    with pytest.raises(local_runtime.ServicesNotStopped):
        wait(runtime, ["agent_nmap_7"])


def testLocalRuntimeResume_whenScanIsPaused_startsItFromItsSnapshotWithItsDefinition(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """The scan starts again under its id with its agents and tracker settings, its snapshot restored once."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    paused_scan = models.Scan.create("test", progress=models.ScanProgress.PAUSED)
    runtime, _ = _paused_runtime(mocker)
    snapshot.save_file(scan_state.snapshot_path(paused_scan.id), UNIVERSE_SNAPSHOT)
    calls = mocker.Mock()
    for name in [
        "_create_network",
        "_start_services",
        "_check_services_healthy",
        "_restore_snapshot",
        "_start_pre_agents",
        "_start_agents",
        "_start_post_agents",
        "_inject_assets",
        "_wait_log_streamer",
    ]:
        mocker.patch.object(runtime, name, getattr(calls, name))
    mocker.patch.object(runtime, "_check_agents_healthy", return_value=True)
    cleanup = mocker.patch.object(runtime, "cleanup", return_value=True)

    resumed_scan = runtime.resume(scan_id=paused_scan.id)

    assert resumed_scan is not None
    assert resumed_scan.id == paused_scan.id
    assert runtime.name == str(paused_scan.id)
    calls._restore_snapshot.assert_called_once_with(UNIVERSE_SNAPSHOT)
    calls._start_agents.assert_called_once_with(SCAN_DEFINITION.agent_group_definition)
    calls._inject_assets.assert_not_called()
    assert runtime.timeout == 600
    assert runtime.init_sleep == 10
    assert runtime.follow == ["agent/ostorlab/nmap"]
    assert _scan_progress(paused_scan.id) == models.ScanProgress.IN_PROGRESS
    assert scan_state.snapshot_path(paused_scan.id).exists() is False
    cleanup.assert_called_once_with(scan_id=paused_scan.id)


def testLocalRuntimeResume_whenPauseLeftResourcesThatCannotBeRemoved_raisesScanResumeError(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """A MQ data volume left by the pause would reload the messages the snapshot restores, the scan is not started."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    paused_scan = models.Scan.create("test", progress=models.ScanProgress.PAUSED)
    runtime, _ = _paused_runtime(mocker)
    snapshot.save_file(scan_state.snapshot_path(paused_scan.id), UNIVERSE_SNAPSHOT)
    mocker.patch.object(runtime, "cleanup", return_value=False)
    start = mocker.patch.object(runtime, "scan")

    with pytest.raises(local_runtime.ScanResumeError):
        runtime.resume(scan_id=paused_scan.id)

    start.assert_not_called()
    assert _scan_progress(paused_scan.id) == models.ScanProgress.PAUSED


def testLocalRuntimeStopServices_always_removesEveryServiceOfTheUniverse(
    mocker: plugin.MockerFixture,
) -> None:
    """The MQ and Redis are removed with their containers before the cleanup removes their volumes."""
    docker_client = mocker.MagicMock()
    runtime = local_runtime.LocalRuntime(scan_id="7")
    runtime._docker_client = docker_client
    mq_service = mocker.MagicMock()
    mq_service.name = "mq_7"
    docker_client.services.list.return_value = [mq_service]
    docker_client.containers.list.return_value = []

    runtime._stop_services()

    docker_client.services.list.assert_called_once_with(
        filters={"label": "ostorlab.universe=7"}
    )
    mq_service.remove.assert_called_once()


def testLocalRuntimeResume_whenScanIsNotPaused_raisesScanResumeError(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Only a paused scan can be resumed."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    scan = models.Scan.create("test", progress=models.ScanProgress.IN_PROGRESS)
    runtime, _ = _paused_runtime(mocker)
    start = mocker.patch.object(runtime, "scan")

    with pytest.raises(local_runtime.ScanResumeError):
        runtime.resume(scan_id=scan.id)

    start.assert_not_called()


def testLocalRuntimeResume_whenScanHasNoSnapshot_raisesScanResumeError(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """A paused scan without snapshot is not restarted from scratch."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    scan = models.Scan.create("test", progress=models.ScanProgress.PAUSED)
    runtime, _ = _paused_runtime(mocker)
    start = mocker.patch.object(runtime, "scan")

    with pytest.raises(local_runtime.ScanResumeError):
        runtime.resume(scan_id=scan.id)

    start.assert_not_called()


def testLocalRuntimeResume_whenStartFails_keepsTheScanPausedWithItsSnapshot(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """A failed resume can be retried: the scan stays paused and keeps its snapshot."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    paused_scan = models.Scan.create("test", progress=models.ScanProgress.PAUSED)
    runtime, _ = _paused_runtime(mocker)
    snapshot.save_file(scan_state.snapshot_path(paused_scan.id), UNIVERSE_SNAPSHOT)
    for name in [
        "_create_network",
        "_start_services",
        "_check_services_healthy",
        "_wait_log_streamer",
        "cleanup",
    ]:
        mocker.patch.object(runtime, name)
    mocker.patch.object(
        runtime,
        "_restore_snapshot",
        side_effect=local_runtime.SnapshotRestoreError("broken"),
    )

    with pytest.raises(local_runtime.SnapshotRestoreError):
        runtime.resume(scan_id=paused_scan.id)

    assert _scan_progress(paused_scan.id) == models.ScanProgress.PAUSED
    assert snapshot.load_file(scan_state.snapshot_path(paused_scan.id)) == (
        UNIVERSE_SNAPSHOT
    )


def testLocalRuntimeLoadSnapshot_whenScanIsResumed_returnsItsLocalSnapshot(
    mocker: plugin.MockerFixture,
) -> None:
    """The snapshot read by `resume` is restored instead of the one of the snapshot storage."""
    load = mocker.patch.object(snapshot, "load")
    runtime = local_runtime.LocalRuntime(
        scan_id="7", snapshot_settings=SNAPSHOT_SETTINGS
    )
    runtime._paused_snapshot = UNIVERSE_SNAPSHOT

    assert runtime._load_snapshot() == UNIVERSE_SNAPSHOT
    load.assert_not_called()


def testRuntimeScanStop_always_removesTheStateOfTheScan(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """A stopped scan cannot be resumed, its definition and snapshot are removed."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    scan = models.Scan.create("test", progress=models.ScanProgress.PAUSED)
    scan_state.save_definition(scan.id, SCAN_DEFINITION)
    runtime = local_runtime.LocalRuntime()
    mocker.patch.object(runtime, "cleanup", return_value=True)

    runtime.stop(scan_id=scan.id)

    assert scan_state.load_definition(scan.id) is None
    assert _scan_progress(scan.id) == models.ScanProgress.STOPPED
