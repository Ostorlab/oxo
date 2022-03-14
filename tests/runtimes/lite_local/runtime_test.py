"""Unittest for lite local runtime."""
import pytest
from docker.models import services as services_model

from ostorlab.runtimes.lite_local import runtime as lite_local_runtime


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
             'Spec': {'Labels': {'ostorlab.universe': '1'}}},
            {'ID': '0099i5n1y3gycuekvksyqyxav',
             'CreatedAt': '2021-12-27T13:37:02.795789947Z',
             'Spec': {'Labels': {'ostorlab.universe': '9999'}}}
        ]

        return [services_model.Service(attrs=service) for service in services]

    mocker.patch('docker.DockerClient.services',
                 return_value=services_model.ServiceCollection())

    mocker.patch('docker.DockerClient.services.list', side_effect=docker_services)
    mocker.patch('docker.models.networks.NetworkCollection.list', return_value=[])
    mocker.patch('docker.models.configs.ConfigCollection.list', return_value=[])

    docker_service_remove = mocker.patch(
        'docker.models.services.Service.remove', return_value=None)
    lite_local_runtime.LiteLocalRuntime(
        scan_id='1', bus_url='bus', bus_vhost='/', bus_management_url='mgmt', bus_exchange_topic='top').stop(
        scan_id='1')

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

    docker_service_remove = mocker.patch(
        'docker.models.services.Service.remove', return_value=None)

    lite_local_runtime.LiteLocalRuntime(
        scan_id='1', bus_url='bus', bus_vhost='/', bus_management_url='mgmt', bus_exchange_topic='topic').stop(
        scan_id='9999')

    docker_service_remove.assert_not_called()
