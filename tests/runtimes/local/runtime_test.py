"""Unittest for local runtime."""

from time import sleep
from typing import Any

import docker
import pytest
from docker.models import services as services_model
from docker.models import networks as networks_model
from pytest_mock import plugin
from unittest import mock

import ostorlab
from ostorlab import exceptions
from ostorlab.assets import android_apk
from ostorlab.runtimes import definitions
from ostorlab.runtimes.local import runtime as local_runtime
from ostorlab.runtimes.local.models import models
from ostorlab.utils import risk_rating as risk_rating_utils


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


def testCheckServicesMethod_whenServicesAreStopped_shouldExit(
    mocker: plugin.MockerFixture, run_scan_mock: None
) -> None:
    """Unit test for Check services method when services are stopped"""
    mocker.patch(
        "ostorlab.runtimes.definitions.AgentSettings.container_image",
        return_value="agent_42_docker_image",
        new_callable=mocker.PropertyMock,
    )
    mocker.patch("ostorlab.runtimes.local.agent_runtime.AgentRuntime")
    mocker.patch("ostorlab.runtimes.local.services.mq.LocalRabbitMQ.is_service_healthy")
    mocker.patch("ostorlab.runtimes.local.services.redis.LocalRedis.is_service_healthy")
    exit_mock = mocker.patch("sys.exit")
    local_runtime_instance = local_runtime.LocalRuntime()
    local_runtime_instance.follow = ["service1"]
    agent_group_definition = definitions.AgentGroupDefinition(
        agents=[definitions.AgentSettings(key="agent/ostorlab/agent42")]
    )

    local_runtime_instance.scan(
        title="test local",
        agent_group_definition=agent_group_definition,
        assets=[android_apk.AndroidApk(content=b"APK")],
    )
    sleep(1)

    assert exit_mock.call_count == 1
    exit_with = exit_mock.call_args_list[0][0][0]
    assert exit_with == 0


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


def testLocalDescribeVuln_whenVulnHasExploitationAndPostExploitationDetails_printsExploitationAndPostExploitationDetails(
    mocker: mock.MagicMock, db_engine_path: str
):
    """Tests describe_vuln method with vulnerability containing exploitation_detail and post_exploitation_detail.
    Should print these details to console.
    """
    mock_console = mock.MagicMock()
    mock_table = mock.MagicMock()
    mock_print = mock.MagicMock()
    mock_success = mock.MagicMock()
    mock_console.table = mock_table
    mock_console.print = mock_print
    mock_console.success = mock_success
    mocker.patch(
        "ostorlab.runtimes.local.runtime.cli_console.Console", return_value=mock_console
    )
    mocker.patch("ostorlab.runtimes.local.runtime.console", mock_console)
    mock_rich_print = mocker.patch("ostorlab.runtimes.local.runtime.rich.print")
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    scan = models.Scan.create(title="Test Scan")
    scan.risk_rating = risk_rating_utils.RiskRating.HIGH
    mock_vulnerability = mock.MagicMock()
    mock_vulnerability.id = 123
    mock_vulnerability.risk_rating.value = "HIGH"
    mock_vulnerability.cvss_v3_vector = "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
    mock_vulnerability.title = "Test Vulnerability"
    mock_vulnerability.short_description = "This is a test vulnerability"
    mock_vulnerability.description = "Detailed description of the vulnerability"
    mock_vulnerability.recommendation = "How to fix the vulnerability"
    mock_vulnerability.references = "Reference: https://example.com"
    mock_vulnerability.technical_detail = "Technical details about the vulnerability"
    mock_vulnerability.location = "Domain: example.com"
    mock_vulnerability.exploitation_detail = "How to exploit this vulnerability"
    mock_vulnerability.post_exploitation_detail = "What to do after exploitation"
    mock_session = mock.MagicMock()
    mock_session.query.return_value.get.return_value = mock_vulnerability
    mock_session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = [
        mock_vulnerability
    ]
    mock_db_context = mock.MagicMock()
    mock_db_context.__enter__.return_value = mock_session
    mocker.patch(
        "ostorlab.runtimes.local.models.models.Database", return_value=mock_db_context
    )
    runtime = local_runtime.LocalRuntime()

    runtime.describe_vuln(scan_id=1, vuln_id=None)

    assert mock_table.call_count == 1
    assert (
        mock_rich_print.call_count >= 6
    )  # At least 6 panels (4 standard + 2 for exploitation details)
    exploitation_panel_calls = [
        call
        for call in mock_rich_print.call_args_list
        if "Exploitation details" in call[0][0].title
        or "Post Exploitation details" in call[0][0].title
    ]
    assert len(exploitation_panel_calls) == 2
    assert mock_success.call_count == 1
