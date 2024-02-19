"""Utils API to play with Docker Volumes."""
import pathlib
import tempfile
from typing import Dict

import docker
from docker import errors as docker_errors


class VolumeWriter:
    """Volume Writer helper class.

    This class uses a temp image to spawn a container with a target volume attached, write content to it using the
    copy API, and then kill everything.
    """

    def __init__(self) -> None:
        self._client = docker.from_env()

    def write(self, volume_name: str, contents: Dict[str, bytes]) -> None:
        """Write content volume at a path.
        Args:
            volume_name: The volume name to create. This command will override existing volumes with the same name.
            contents: Dict of a path where the content will be written to in the volume and content in bytes format.
        Returns:
            None
        """
        try:
            self._client.volumes.get(volume_name).remove()
        except docker_errors.NotFound:
            pass

        # Create a new directory in the system's temporary directory
        volume_path = pathlib.Path(tempfile.gettempdir()) / volume_name
        volume_path.mkdir(parents=True, exist_ok=True)
        for path, content in contents.items():
            with open(volume_path / path, "ab") as file:
                file.write(content)
        self._client.volumes.create(
            volume_name,
            driver="local",
            driver_opts={"type": "none", "device": str(volume_path), "o": "bind"},
        )


def create_volume(volume_name: str, contents: Dict[str, bytes]) -> None:
    """Poor man's API to create a volume and persist content.

    Docker do not provide an API to write directly to volume, most likely due to the plugin support, even though that
     should not make it impossible.
    This API is big `hack`, that start a temporary container to copy content to it. The destination is the volume mount
    point.

    Args:
        volume_name: The volume name to create. This command will override existing volumes with the same name.
        contents: Dict of path where the content will written to in the volume and content in bytes format.

    Returns:
        None
    """
    VolumeWriter().write(volume_name, contents)
