"""Unit tests for volume utils."""

import docker
import pytest
from docker import types as docker_types

from ostorlab.utils import volumes


@pytest.mark.docker
def testWriteContentVolume_always_contentIsPersistedToVolume():
    """Creates a volumes, a check its content by reading it using a mounted container."""
    volumes.create_volume(
        "unitest_ostorlab_volume",
        {"test": b"Cat is alive! :)", "notest": b"Cat is dead! :("},
    )

    client = docker.from_env()
    out = client.containers.run(
        "busybox:latest",
        stderr=True,
        stdout=True,
        detach=False,
        remove=True,
        command="cat /output/test",
        mounts=[
            docker_types.Mount(
                target="/output", source="unitest_ostorlab_volume", type="volume"
            )
        ],
    )

    assert out == b"Cat is alive! :)"


def testCreateVolume_whenVolumeNotFound_createsNewVolume(mocker):
    """When existing volume is not found, creates new volume without error."""
    mock_client = mocker.MagicMock()
    mock_client.volumes.get.side_effect = docker.errors.NotFound("Volume not found")
    writer = volumes.VolumeWriter()
    writer._client = mock_client

    writer._create_volume("test_vol", labels={"a": "b"})

    mock_client.volumes.create.assert_called_once_with(
        name="test_vol", labels={"a": "b"}
    )


def testCreateVolume_whenVolumeRemovalRaisesAPIError_raisesException(mocker):
    """When existing volume removal fails with APIError, exception is raised and volume is not created."""
    mock_client = mocker.MagicMock()
    mock_volume = mocker.MagicMock()
    mock_volume.remove.side_effect = docker.errors.APIError("Volume in use")
    mock_client.volumes.get.return_value = mock_volume
    writer = volumes.VolumeWriter()
    writer._client = mock_client

    with pytest.raises(docker.errors.APIError):
        writer._create_volume("test_vol")

    mock_client.volumes.create.assert_not_called()
