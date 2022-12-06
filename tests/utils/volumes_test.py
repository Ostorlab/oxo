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
