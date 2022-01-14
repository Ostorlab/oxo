"""Unittest for local runtime."""
import docker
import pytest

from ostorlab.assets import android_apk
from ostorlab.runtimes import definitions
from ostorlab.runtimes.local import runtime as local_runtime
from docker.models import services as services_model

@pytest.mark.skip(reason='Missing inject asset agent.')
@pytest.mark.docker
def testRuntimeScan_whenEmptyRunDefinition_runtimeServicesAreRunning():
    local_runtime_instance = local_runtime.LocalRuntime()
    asset = android_apk.AndroidApk(content=b'APK')
    agent_group_definition = definitions.AgentGroupDefinition(agents=[])

    local_runtime_instance.scan(agent_group_definition=agent_group_definition, asset=asset)

    docker_client = docker.from_env()

    services = docker_client.services.list(filters={'label': f'ostorlab.universe={local_runtime_instance.name}'})
    assert any(s.name.startswith('mq_') for s in services)


@pytest.mark.skip(reason='Missing sample agents to test with.')
@pytest.mark.docker
def testRuntimeScan_whenValidAgentRunDefinitionAndAssetAreProvided_scanIsRunning():
    local_runtime_instance = local_runtime.LocalRuntime()
    asset = android_apk.AndroidApk(content=b'APK')
    agent_group_definition = definitions.AgentGroupDefinition(agents=[])

    local_runtime_instance.scan(agent_group_definition=agent_group_definition, asset=asset)

    docker_client = docker.from_env()

    services = docker_client.services.list(filters={'label': f'ostorlab.universe={local_runtime_instance.name}'})
    assert any(s.name.startswith('mq_') for s in services)
    assert any(s.name.starts_with('agent_') for s in services)
    # TODO(alaeddine): check for asset injection.
    configs = docker_client.configs.list()
    assert any(c.name.starts_with('agent_') for c in configs)


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
            {'ID': '0099i5n1y3gycuekvksyqyxav',
             'CreatedAt': '2021-12-27T13:37:02.795789947Z',
             'Spec': {'Labels': {'ostorlab.universe': 'qmwjef'}}},
            {'ID': '0099i5n1y3gycuekvksyqyxav',
             'CreatedAt': '2021-12-27T13:37:02.795789947Z',
             'Spec': {'Labels': {'ostorlab.universe': 'fejwmq'}}}
        ]

        return [services_model.Service(attrs=service) for service in services]

    mocker.patch('docker.DockerClient.services',
                 return_value=services_model.ServiceCollection())
    mocker.patch('docker.DockerClient.services.list', side_effect=docker_services)
    docker_service_remove = mocker.patch('docker.models.services.Service.remove', return_value=None)

    local_runtime.LocalRuntime().stop(scan_id='qmwjef')

    docker_service_remove.assert_called_once()


@pytest.mark.docker
def testRuntimeScanStop_whenScanIdIsInvalid_DoesNotRemoveAnyService(mocker):
    """Unittest for the scan stop method when the scan id is invalid.
    Gets the docker services and checks for those with ostorlab.universe
    as one of the labels to find the service with the given scan id.
    Does not remove any service.
    """
    def docker_services():
        """Method for mocking the services list response."""

        services = [
            {'ID': '0099i5n1y3gycuekvksyqyxav',
             'CreatedAt': '2021-12-27T13:37:02.795789947Z',
             'Spec': {'Labels': {'ostorlab.universe': 'qmwjef'}}},
            {'ID': '0099i5n1y3gycuekvksyqyxav',
             'CreatedAt': '2021-12-27T13:37:02.795789947Z',
             'Spec': {'Labels': {'ostorlab.universe': 'fejwmq'}}}
        ]

        return [services_model.Service(attrs=service) for service in services]

    mocker.patch('docker.DockerClient.services',
                 return_value=services_model.ServiceCollection())
    mocker.patch('docker.DockerClient.services.list', side_effect=docker_services)
    docker_service_remove = mocker.patch('docker.models.services.Service.remove', return_value=None)

    local_runtime.LocalRuntime().stop(scan_id='iiippp')

    docker_service_remove.assert_not_called()
def testRuntimeScanList_whenScansArePresent_showsScans(mocker):
    """Unittest for the scan list method when there are local scans available.
    Gets the docker services and checks for those with ostorlab.universe
    as one of the labels.
    Shows the list of scans.
    """

    def docker_services():
        """Method for mocking the scan list response."""
        services = [
            {'ID': '0099i5n1y3gycuekvksyqyxav',
                             'CreatedAt': '2021-12-27T13:37:02.795789947Z',
                             'Spec': {'Labels': {'ostorlab.universe': 'qmwjef'}}},
            {'ID': '0099i5n1y3gycuekvksyqyxav',
             'CreatedAt': '2021-12-27T13:37:02.795789947Z',
             'Spec': {'Labels': {'ostorlab.mq': ''}}}
                             ]

        return [services_model.Service(attrs=service) for service in services]

    mocker.patch('docker.DockerClient.services', return_value=services_model.ServiceCollection())
    mocker.patch('docker.DockerClient.services.list', side_effect=docker_services)

    scans = local_runtime.LocalRuntime().list()

    assert len(scans) == 1
    assert scans[0].id == 'qmwjef'
    assert scans[0].created_time == '2021-12-27T13:37:02.795789947Z'


@pytest.mark.docker
def testRuntimeScanList_whenScansAreNotPresent_showsEmptyList(mocker):
    """Unittest for the scan list method when there are no local scans available.
    Gets the docker services and checks for those with ostorlab.universe
    as one of the labels.
    Shows an empty list.
    """

    mocker.patch('docker.DockerClient.services', return_value=services_model.ServiceCollection())
    mocker.patch('docker.DockerClient.services.list', side_effect=lambda:[])

    scans = local_runtime.LocalRuntime().list()

    assert len(scans) == 0
