"""Utils API to play with Docker Volumes."""

import io
import tarfile
import time

from typing import Dict
import docker
from docker import types as docker_types
from docker import errors as docker_errors

from ostorlab.utils import strings

TEMP_IMAGE = "busybox:latest"
TEMP_DESTINATION = "/dst"


class VolumeWriter:
    """Volume Writer helper class.

    This class uses a temp image to spawn a container with a target volume attached, write content to it using the
    copy API, and then kill everything.
    """

    def __init__(self) -> None:
        self._client = docker.from_env()

    def write(self, volume_name: str, contents: Dict[str, bytes]) -> None:
        """Write content volume at path.

        Args:
            volume_name: The volume name to create. This command will override existing volumes with the same name.
            contents: Dict of path where the content will written to in the volume and content in bytes format.
        Returns:
            None
        """
        self._install_image()
        self._create_volume(volume_name)
        self._write_content(volume_name, contents)

    def _install_image(self) -> None:
        """Installs a busybox image for the form."""
        self._client.images.pull(TEMP_IMAGE)

    def _create_volume(self, name: str) -> None:
        """Override existing images."""
        try:
            self._client.volumes.get(name).remove()
        except docker_errors.NotFound:
            pass
        self._client.volumes.create(name)

    def _prepare_tar(self, contents: Dict[str, bytes]) -> io.BytesIO:
        """Copy API expects a tar, this api prepares one with the file content."""
        pw_tarstream = io.BytesIO()
        with tarfile.TarFile(fileobj=pw_tarstream, mode="w") as pw_tar:
            for path, content in contents.items():
                tarinfo = tarfile.TarInfo(name=path)
                tarinfo.size = len(content)
                tarinfo.mtime = int(time.time())
                pw_tar.addfile(tarinfo, io.BytesIO(content))
        pw_tarstream.seek(0)
        return pw_tarstream

    def _write_content(self, volume_name: str, contents: Dict[str, bytes]) -> None:
        """Use the docker copy API to write content to target volume."""
        temp_container_name = strings.random_string(9)
        self._client.containers.run(
            TEMP_IMAGE,
            name=temp_container_name,
            command="sleep infinity",
            detach=True,
            remove=True,
            mounts=[
                docker_types.Mount(
                    target=TEMP_DESTINATION, source=volume_name, type="volume"
                )
            ],
        )
        pw_tarstream = self._prepare_tar(contents)

        container = self._client.containers.get(temp_container_name)
        container.put_archive(TEMP_DESTINATION, pw_tarstream)
        container.stop(timeout=0)


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
