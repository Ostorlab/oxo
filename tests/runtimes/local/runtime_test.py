"""Unittest for local runtime."""
import docker
import pytest
import sys
import ostorlab
from ostorlab.assets import android_apk
from ostorlab.runtimes import definitions
from ostorlab.runtimes.local import runtime as local_runtime
from ostorlab.runtimes.local.models import models
from docker.models import services as services_model


@pytest.mark.skip(reason='Missing inject asset agent.')
@pytest.mark.docker
def testRuntimeScan_whenEmptyRunDefinition_runtimeServicesAreRunning():
    local_runtime_instance = local_runtime.LocalRuntime()
    asset = android_apk.AndroidApk(content=b'APK')
    agent_group_definition = definitions.AgentGroupDefinition(agents=[])

    local_runtime_instance.scan(title='test local', agent_group_definition=agent_group_definition, assets=[asset])

    docker_client = docker.from_env()

    services = docker_client.services.list(filters={'label': f'ostorlab.universe={local_runtime_instance.name}'})
    assert any(s.name.startswith('mq_') for s in services)


@pytest.mark.skip(reason='Missing sample agents to test with.')
@pytest.mark.docker
def testRuntimeScan_whenValidAgentRunDefinitionAndAssetAreProvided_scanIsRunning():
    local_runtime_instance = local_runtime.LocalRuntime()
    asset = android_apk.AndroidApk(content=b'APK')
    agent_group_definition = definitions.AgentGroupDefinition(agents=[])

    local_runtime_instance.scan(title='test local', agent_group_definition=agent_group_definition, assets=[asset])

    docker_client = docker.from_env()

    services = docker_client.services.list(filters={'label': f'ostorlab.universe={local_runtime_instance.name}'})
    assert any(s.name.startswith('mq_') for s in services)
    assert any(s.name.starts_with('agent_') for s in services)
    # TODO(alaeddine): check for asset injection.
    configs = docker_client.configs.list()
    assert any(c.name.starts_with('agent_') for c in configs)


@pytest.mark.docker
def testRuntimeScanStop_whenScanIdIsValid_RemovesScanService(mocker, tmpdir):
    """Unittest for the scan stop method when there are local scans available.
    Gets the docker services and checks for those with ostorlab.universe
    as one of the labels to find the service with the given scan id.
    Removes the scan service matching the provided id.
    """

    if sys.platform == 'win32':
        path = f'sqlite:///{tmpdir}\\ostorlab_db1.sqlite'.replace('\\', '\\\\')
    else:
        path = f'sqlite:////{tmpdir}/ostorlab_db1.sqlite'

    mocker.patch.object(models, 'ENGINE_URL', f'{path}')
    models.Database().create_db_tables()
    create_scan_db = models.Scan.create('test')
    def docker_services():
        """Method for mocking the services list response."""
        scan = models.Database().session.query(models.Scan).first()
        services = [
            {'ID': '0099i5n1y3gycuekvksyqyxav',
             'CreatedAt': '2021-12-27T13:37:02.795789947Z',
             'Spec': {'Labels': {'ostorlab.universe': scan.id}}},
            {'ID': '0099i5n1y3gycuekvksyqyxav',
             'CreatedAt': '2021-12-27T13:37:02.795789947Z',
             'Spec': {'Labels': {'ostorlab.universe': 9999}}}
        ]

        return [services_model.Service(attrs=service) for service in services]

    mocker.patch('docker.DockerClient.services',
                 return_value=services_model.ServiceCollection())

    mocker.patch('docker.DockerClient.services.list', side_effect=docker_services)
    mocker.patch('docker.models.networks.NetworkCollection.list', return_value=[])
    mocker.patch('docker.models.configs.ConfigCollection.list', return_value=[])

    docker_service_remove = mocker.patch('docker.models.services.Service.remove', return_value=None)
    local_runtime.LocalRuntime().stop(scan_id=create_scan_db.id)

    docker_service_remove.assert_called_once()


@pytest.mark.docker
def testRuntimeScanStop_whenScanIdIsInvalid_DoesNotRemoveAnyService(mocker, db_engine_path):
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
             'Spec': {'Labels': {'ostorlab.universe': '1'}}},
            {'ID': '0099i5n1y3gycuekvksyqyxav',
             'CreatedAt': '2021-12-27T13:37:02.795789947Z',
             'Spec': {'Labels': {'ostorlab.universe': '2'}}}
        ]

        return [services_model.Service(attrs=service) for service in services]

    mocker.patch('docker.DockerClient.services',
                 return_value=services_model.ServiceCollection())
    mocker.patch('docker.DockerClient.services.list', side_effect=docker_services)
    mocker.patch('docker.models.networks.NetworkCollection.list', return_value=[])
    mocker.patch('docker.models.configs.ConfigCollection.list', return_value=[])

    docker_service_remove = mocker.patch('docker.models.services.Service.remove', return_value=None)

    mocker.patch.object(models, 'ENGINE_URL', db_engine_path)
    models.Database().create_db_tables()
    create_scan_db = models.Scan.create('test')
    local_runtime.LocalRuntime().stop(scan_id=create_scan_db.id)

    local_runtime.LocalRuntime().stop(scan_id='9999')

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
            {'ID': '0099i5n1y3gycuekvksyqyxav',
             'CreatedAt': '2021-12-27T13:37:02.795789947Z',
             'Spec': {'Labels': {'ostorlab.universe': '1'}}},
            {'ID': '0099i5n1y3gycuekvksyqyxav',
             'CreatedAt': '2021-12-27T13:37:02.795789947Z',
             'Spec': {'Labels': {'ostorlab.mq': ''}}}
        ]

        return [services_model.Service(attrs=service) for service in services]

    mocker.patch.object(ostorlab.runtimes.local.models.models, 'ENGINE_URL', db_engine_path)
    mocker.patch('ostorlab.runtimes.local.LocalRuntime.__init__', return_value=None)
    mocker.patch('docker.DockerClient.services', return_value=services_model.ServiceCollection())
    mocker.patch('docker.DockerClient.services.list', side_effect=docker_services)

    scans = local_runtime.LocalRuntime().list()

    assert len(scans) == 0
