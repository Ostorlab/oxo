"""Unit tests for shared docker_cleanup module."""

from unittest import mock

from docker import errors as docker_errors
from requests import exceptions as requests_exceptions

from ostorlab.runtimes import docker_cleanup


def testCleanupScanDockerResources_whenScanIdNoneOrEmpty_returnsTrue() -> None:
    """When scan_id is None or empty string, cleanup immediately returns True without querying client."""
    mock_client = mock.MagicMock()

    assert docker_cleanup.cleanup_scan_docker_resources(mock_client, None) is True
    assert docker_cleanup.cleanup_scan_docker_resources(mock_client, "") is True
    assert docker_cleanup.cleanup_scan_docker_resources(mock_client, "   ") is True

    mock_client.services.list.assert_not_called()
    mock_client.networks.list.assert_not_called()
    mock_client.configs.list.assert_not_called()
    mock_client.volumes.list.assert_not_called()


def testCleanupScanDockerResources_whenResourcesMatch_removesMatchingOnlyAndReturnsTrue() -> (
    None
):
    """Matching services, networks, configs, and volumes are removed and returns True."""
    mock_client = mock.MagicMock()

    matching_service = mock.MagicMock(
        attrs={"Spec": {"Labels": {"ostorlab.universe": "scan_42"}}}
    )
    non_matching_service = mock.MagicMock(
        attrs={"Spec": {"Labels": {"ostorlab.universe": "other_scan"}}}
    )
    mock_client.services.list.return_value = [matching_service, non_matching_service]

    matching_network = mock.MagicMock(
        attrs={"Labels": {"ostorlab.universe": "scan_42"}}
    )
    non_matching_network = mock.MagicMock(
        attrs={"Labels": {"ostorlab.universe": "other_scan"}}
    )
    mock_client.networks.list.return_value = [matching_network, non_matching_network]

    matching_config = mock.MagicMock(
        attrs={"Spec": {"Labels": {"ostorlab.universe": "scan_42"}}}
    )
    non_matching_config = mock.MagicMock(
        attrs={"Spec": {"Labels": {"ostorlab.universe": "other_scan"}}}
    )
    mock_client.configs.list.return_value = [matching_config, non_matching_config]

    matching_volume = mock.MagicMock(
        attrs={"Labels": {"ostorlab.universe": "scan_42"}, "Name": "vol1"}
    )
    matching_named_volume = mock.MagicMock(
        attrs={"Labels": {}, "Name": "asset_scan_42"}
    )
    matching_named_volume.name = "asset_scan_42"
    non_matching_volume = mock.MagicMock(
        attrs={"Labels": {"ostorlab.universe": "other"}, "Name": "vol2"}
    )
    non_matching_volume.name = "vol2"
    mock_client.volumes.list.return_value = [
        matching_volume,
        matching_named_volume,
        non_matching_volume,
    ]

    success = docker_cleanup.cleanup_scan_docker_resources(mock_client, "scan_42")

    assert success is True
    matching_service.remove.assert_called_once()
    non_matching_service.remove.assert_not_called()
    matching_network.remove.assert_called_once()
    non_matching_network.remove.assert_not_called()
    matching_config.remove.assert_called_once()
    non_matching_config.remove.assert_not_called()
    matching_volume.remove.assert_called_once_with()
    matching_named_volume.remove.assert_called_once_with()
    non_matching_volume.remove.assert_not_called()


def testCleanupScanDockerResources_whenServiceRemovalFails_continuesAndReturnsFalse() -> (
    None
):
    """When a service removal fails with DockerException, other resources are still cleaned up and False is returned."""
    mock_client = mock.MagicMock()

    failing_service = mock.MagicMock(
        attrs={"Spec": {"Labels": {"ostorlab.universe": "100"}}}
    )
    failing_service.remove.side_effect = docker_errors.DockerException("removal failed")

    succeeding_network = mock.MagicMock(attrs={"Labels": {"ostorlab.universe": "100"}})

    mock_client.services.list.return_value = [failing_service]
    mock_client.networks.list.return_value = [succeeding_network]
    mock_client.configs.list.return_value = []
    mock_client.volumes.list.return_value = []

    success = docker_cleanup.cleanup_scan_docker_resources(mock_client, 100)

    assert success is False
    assert failing_service.remove.call_count == 3
    succeeding_network.remove.assert_called_once()


def testCleanupScanDockerResources_whenListRaisesDockerException_returnsFalse() -> None:
    """When services.list() raises DockerException, cleanup catches it and returns False."""
    mock_client = mock.MagicMock()
    mock_client.services.list.side_effect = docker_errors.DockerException(
        "daemon error"
    )
    mock_client.networks.list.return_value = []
    mock_client.configs.list.return_value = []
    mock_client.volumes.list.return_value = []

    success = docker_cleanup.cleanup_scan_docker_resources(mock_client, "100")

    assert success is False


def testCleanupScanDockerResources_whenResourceRaisesNotFound_returnsTrue() -> None:
    """When a resource removal raises NotFound (already removed), it is not treated as an error and returns True."""
    mock_client = mock.MagicMock()

    service = mock.MagicMock(attrs={"Spec": {"Labels": {"ostorlab.universe": "100"}}})
    service.remove.side_effect = docker_errors.NotFound("service not found")

    network = mock.MagicMock(attrs={"Labels": {"ostorlab.universe": "100"}})
    network.remove.side_effect = docker_errors.NotFound("network not found")

    config = mock.MagicMock(attrs={"Spec": {"Labels": {"ostorlab.universe": "100"}}})
    config.remove.side_effect = docker_errors.NotFound("config not found")

    volume = mock.MagicMock(attrs={"Labels": {"ostorlab.universe": "100"}})
    volume.remove.side_effect = docker_errors.NotFound("volume not found")

    mock_client.services.list.return_value = [service]
    mock_client.networks.list.return_value = [network]
    mock_client.configs.list.return_value = [config]
    mock_client.volumes.list.return_value = [volume]

    success = docker_cleanup.cleanup_scan_docker_resources(mock_client, "100")

    assert success is True
    service.remove.assert_called_once()
    network.remove.assert_called_once()
    config.remove.assert_called_once()
    volume.remove.assert_called_once_with()


def testCleanupScanDockerResources_whenResourceRaisesAPIError_handlesErrorAndReturnsFalse() -> (
    None
):
    """When a resource list or removal raises APIError, cleanup catches it and returns False."""
    mock_client = mock.MagicMock()
    mock_response = mock.MagicMock(status_code=500, content=b"Server error")
    mock_client.services.list.side_effect = docker_errors.APIError(
        "API error", response=mock_response
    )
    mock_client.networks.list.return_value = []
    mock_client.configs.list.return_value = []
    mock_client.volumes.list.return_value = []

    success = docker_cleanup.cleanup_scan_docker_resources(mock_client, "100")

    assert success is False


def testCleanupScanDockerResources_whenNamedVolumeGetRaisesAPIError_handlesErrorAndReturnsFalse() -> (
    None
):
    """When volumes.get raises APIError for named volumes, cleanup catches it and returns False."""
    mock_client = mock.MagicMock()
    mock_client.services.list.return_value = []
    mock_client.networks.list.return_value = []
    mock_client.configs.list.return_value = []
    mock_client.volumes.list.return_value = []
    mock_client.volumes.get.side_effect = docker_errors.DockerException(
        "Failed to get volume"
    )

    success = docker_cleanup.cleanup_scan_docker_resources(mock_client, "100")

    assert success is False


def testCleanupScanDockerResources_whenScanIdIsLiteralNoneString_returnsTrueWithoutQueryingClient() -> (
    None
):
    """When scan_id is literal 'None', cleanup immediately returns True without querying client."""
    mock_client = mock.MagicMock()

    assert docker_cleanup.cleanup_scan_docker_resources(mock_client, "None") is True

    mock_client.services.list.assert_not_called()
    mock_client.networks.list.assert_not_called()
    mock_client.configs.list.assert_not_called()
    mock_client.volumes.list.assert_not_called()


def testCleanupScanDockerResources_whenResourceHasNoUniverseLabel_isNotRemoved() -> (
    None
):
    """Resources without universe label are not removed even if returned by list."""
    mock_client = mock.MagicMock()
    service_without_label = mock.MagicMock(attrs={"Spec": {"Labels": None}})
    service_with_other_label = mock.MagicMock(
        attrs={"Spec": {"Labels": {"other": "label"}}}
    )
    mock_client.services.list.return_value = [
        service_without_label,
        service_with_other_label,
    ]
    mock_client.networks.list.return_value = []
    mock_client.configs.list.return_value = []
    mock_client.volumes.list.return_value = []

    success = docker_cleanup.cleanup_scan_docker_resources(mock_client, "123")

    assert success is True
    service_without_label.remove.assert_not_called()
    service_with_other_label.remove.assert_not_called()


def testCleanupScanDockerResources_whenRequestExceptionRaised_handlesErrorAndReturnsFalse() -> (
    None
):
    """When a requests ConnectionError/RequestException occurs, cleanup catches it and returns False."""
    mock_client = mock.MagicMock()
    mock_client.services.list.side_effect = requests_exceptions.ConnectionError(
        "Connection refused"
    )
    mock_client.networks.list.return_value = []
    mock_client.configs.list.return_value = []
    mock_client.volumes.list.return_value = []

    success = docker_cleanup.cleanup_scan_docker_resources(mock_client, "100")

    assert success is False
