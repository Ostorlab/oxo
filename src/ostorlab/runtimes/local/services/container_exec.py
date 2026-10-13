"""Run a command inside the running container of a service, like the MQ readiness check does.

Used to restore the state of a paused universe in its MQ and Redis services: the runtime may run outside the universe
network, so it reaches the services through docker instead of their network address.
"""

from __future__ import annotations

import io
import logging
import tarfile
import typing

import docker
from docker import errors
from docker.models import services

from ostorlab import exceptions

logger = logging.getLogger(__name__)

# Directory of the files copied to the container, it exists in the MQ and Redis images.
FILES_DIRECTORY = "/tmp"


class ExecError(exceptions.OstorlabError):
    """The command could not run in the service container or failed."""


def run(
    docker_client: docker.DockerClient,
    service: services.Service | None,
    command: list[str],
    files: dict[str, bytes] | None = None,
) -> bytes:
    """Copy files to `FILES_DIRECTORY` of the running container of a service, then run a command in it.

    Args:
        docker_client: Docker client.
        service: The service, with a single replica.
        command: The command to run.
        files: Content of the files to copy, by file name.

    Returns:
        The output of the command.

    Raises:
        ExecError: When the service has no running container, or the command fails.
    """
    if service is None:
        raise ExecError("service is not started.")
    try:
        running_tasks = [
            task
            for task in typing.cast(
                typing.Callable[[], list[dict[str, typing.Any]]], service.tasks
            )()
            if task["Status"]["State"] == "running"
        ]
        if len(running_tasks) != 1:
            raise ExecError(
                f"service {service.name} has {len(running_tasks)} running containers."
            )
        container = docker_client.containers.get(
            running_tasks[0]["Status"]["ContainerStatus"]["ContainerID"]
        )
        if files is not None:
            container.put_archive(FILES_DIRECTORY, _archive(files))
        result = container.exec_run(command)
    except (errors.DockerException, KeyError) as e:
        raise ExecError(f"could not run {command[0]} in {service.name}: {e}") from e
    output = typing.cast(bytes, result.output)
    if result.exit_code != 0:
        raise ExecError(
            f"{command[0]} failed in {service.name} with exit code {result.exit_code}: "
            f"{output.decode(errors='replace')}"
        )
    return output


def _archive(files: dict[str, bytes]) -> bytes:
    """Tar archive of the files, the format `put_archive` expects."""
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as archive:
        for name, content in files.items():
            info = tarfile.TarInfo(name=name)
            info.size = len(content)
            archive.addfile(info, io.BytesIO(content))
    return buffer.getvalue()
