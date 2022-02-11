"""Check if requirements for running docker are satisfied."""

import docker

def is_docker_installed():
    """Checks if docker is installed"""
    try:
        _ = docker.from_env()
    except docker.errors.DockerException as e:
        if 'ConnectionRefusedError' in str(e):
            return False
    return True

def is_user_permitted():
    """Check if the user got permissions to run docker."""
    try:
        _ = docker.from_env()
    except docker.errors.DockerException as e:
        if 'PermissionError' in str(e):
            return False
    return True

def is_swarm_initialized():
    """Checks if docker swarm is initialized."""
    if is_user_permitted():
        docker_client = docker.from_env()
        if len(docker_client.swarm.attrs.keys()) == 0:
            return False
        return True

def init_swarm():
    """Initialize swarm"""
    if is_user_permitted():
        docker_client = docker.from_env()
        docker_client.swarm.init()
