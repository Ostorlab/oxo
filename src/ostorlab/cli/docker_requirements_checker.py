"""Check if requirements for running docker are satisfied."""

import platform
import sys

import docker
import tenacity
from docker import errors

from ostorlab import exceptions

_SUPPORTED_ARCH_TYPES = ["x86_64", "AMD64", "arm64", "aarch64"]
RETRY_ATTEMPTS = 10
WAIT_TIME = 2
MULTIPLE_ADVERTISE_ADDRESSES_ERROR = "could not choose an IP address to advertise"
LOCAL_ADVERTISE_ADDRESS = "127.0.0.1"

# The architecture is checked with a return value that's based on the kernel implementation of the uname(2)
# system call. So it might be necessary to handle the same arch with various strings e.g. linux returns x86_64
# or AMD64 on windows.


def is_docker_installed() -> bool:
    """Checks if docker is installed

    Returns:
        True if docker is installed, else False
    """
    try:
        _ = docker.from_env()
    except errors.DockerException as e:
        if "ConnectionRefusedError" in str(e):
            return False
    return True


def is_sys_arch_supported() -> bool:
    """Checks if the systems cpu architecture is supported

    Returns:
        True if the architecture is supported, else False
    """
    return platform.machine() in _SUPPORTED_ARCH_TYPES


def is_user_permitted() -> bool:
    """Check if the user got permissions to run docker.

    Returns:
        True if user has permission to run docker, else False
    """
    try:
        _ = docker.from_env()
    except errors.DockerException as e:
        if "PermissionError" in str(e):
            return False
    return True


def is_docker_working() -> bool:
    """Last hope check to see if docker works without being able to give an intelligible recommendation.

    Returns:
        True if user has permission to run docker, else False
    """
    if sys.platform == "win32":
        import pywintypes

        try:
            client = docker.from_env()
            client.ping()
        except errors.DockerException:
            return False
        except pywintypes.error:
            return False
    else:
        try:
            client = docker.from_env()
            client.ping()
        except errors.DockerException:
            return False
    return True


def is_swarm_initialized() -> bool:
    """Checks if docker swarm is initialized.

    Returns:
        True if docker swarm is initialized, else False
    """
    if is_user_permitted():
        docker_client = docker.from_env()
        return docker_client.swarm.id is not None
    else:
        return False


def init_swarm() -> None:
    """Initializes Docker Swarm.

    This function attempts to initialize Docker Swarm. If the initialization fails,
    it retries 10 times with a 2-second  delay between each attempt.
    If it still fails after 10 attempts, it raises an OstorlabError.

    Raises:
        OstorlabError: If the user does not have permission to run Docker,
        or if the initialization fails after 10 attempts.
    """
    if is_user_permitted() is False:
        raise errors.DockerException("User does not have permission to run docker.")
    try:
        _init_swarm()
    except errors.DockerException as e:
        raise exceptions.OstorlabError("Error while initializing swarm.") from e


@tenacity.retry(
    stop=tenacity.stop_after_attempt(RETRY_ATTEMPTS),
    wait=tenacity.wait_fixed(WAIT_TIME),
    retry=tenacity.retry_if_exception_type(errors.DockerException),
    reraise=True,
)
def _init_swarm() -> None:
    """Initialize docker swarm.

    Docker refuses to pick an advertise address when the default interface has several addresses. The local
    runtime runs a single-node swarm, so the loopback address is used in that case.
    """
    docker_client = docker.from_env()
    try:
        docker_client.swarm.init()
    except errors.APIError as e:
        if MULTIPLE_ADVERTISE_ADDRESSES_ERROR not in str(e):
            raise
        docker_client.swarm.init(advertise_addr=LOCAL_ADVERTISE_ADDRESS)
