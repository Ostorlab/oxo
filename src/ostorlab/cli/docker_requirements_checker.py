"""Check if requirements for running docker are satisfied."""

import docker
import platform
import sys
from docker import errors

_SUPPORTED_ARCH_TYPES = ['x86_64', 'AMD64']
# The architecture is checked with a return value that's based on the kernel implementation of the uname(2)
# system call. So it might be necesarry to handle the same arch with various strings e.g. linux returns x86_64
# or AMD64 on windows.

def is_docker_installed() -> bool:
    """Checks if docker is installed

    Returns:
        True if docker is installed, else False
    """
    try:
        _ = docker.from_env()
    except errors.DockerException as e:
        if 'ConnectionRefusedError' in str(e):
            return False
    return True

def is_sys_arch_supported() -> bool:
    """Checks if the systems cpu architecture is supported

    Returns:
        True if the architecture is supported, else False
    """
    if sys.platform == 'darwin' and 'ARM' in platform.version():
        # On mac os, uname returns x86 even on arm64 if the process calling it is running via rosetta. We parse for ARM
        # in platform.version() to determine the arch on mac os
        return False
    else:
        if platform.machine() not in _SUPPORTED_ARCH_TYPES:
            return False
    return True

def is_user_permitted() -> bool:
    """Check if the user got permissions to run docker.

    Returns:
        True if user has permission to run docker, else False
    """
    try:
        _ = docker.from_env()
    except errors.DockerException as e:
        if 'PermissionError' in str(e):
            return False
    return True


def is_docker_working() -> bool:
    """Last hope check to see if docker works without being able to give an intelligible recommendation.

    Returns:
        True if user has permission to run docker, else False
    """
    if sys.platform == 'win32':
        import pywintypes  # pylint: disable=import-outside-toplevel
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
        if docker_client.swarm.id is None:
            return False
        else:
            return True
    else:
        return False


def init_swarm() -> None:
    """Initialize docker swarm"""
    if is_user_permitted():
        docker_client = docker.from_env()
        docker_client.swarm.init()
