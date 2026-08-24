"""Helper module for cleaning up Docker resources belonging to a scan universe."""

import logging
from typing import Any

from docker import errors as docker_errors

from ostorlab.cli import console as cli_console

logger = logging.getLogger(__name__)
console = cli_console.Console()


def cleanup_scan_docker_resources(
    docker_client: Any, scan_id: int | str | None
) -> bool:
    """Remove all Docker services, networks, configs, and volumes belonging to universe with scan_id.

    Args:
        docker_client: The Docker client instance to use for resource removal.
        scan_id: The scan/universe identifier.

    Returns:
        bool: True if cleanup completed without error, False otherwise.
    """
    if scan_id is None or str(scan_id).strip() == "":
        logger.warning("No valid scan_id provided for Docker resource cleanup.")
        return True

    scan_id_str = str(scan_id)
    logger.info("Cleaning up scan resources for universe %s", scan_id_str)
    stopped_services = []
    stopped_network = []
    stopped_configs = []
    stopped_volumes = []
    had_errors = False

    try:
        services = docker_client.services.list()
    except docker_errors.DockerException as e:
        had_errors = True
        logger.warning("Failed to list Docker services: %s", e)
        services = []
    for service in services:
        try:
            service_attrs = getattr(service, "attrs", None) or {}
            service_spec = (
                service_attrs.get("Spec")
                if isinstance(service_attrs.get("Spec"), dict)
                else {}
            )
            service_labels = (
                service_spec.get("Labels")
                if isinstance(service_spec.get("Labels"), dict)
                else {}
            ) or {}
            universe_label = service_labels.get("ostorlab.universe")
            if (
                universe_label == scan_id
                or universe_label == scan_id_str
                or str(universe_label) == scan_id_str
            ):
                service_name = (
                    service_spec.get("Name")
                    or service_attrs.get("Name")
                    or getattr(service, "id", "")
                )
                logger.info("Removing service: %s", service_name)
                stopped_services.append(service)
                service.remove()
        except docker_errors.DockerException as e:
            had_errors = True
            logger.warning("Failed to remove service: %s", e)

    try:
        networks = docker_client.networks.list()
    except docker_errors.DockerException as e:
        had_errors = True
        logger.warning("Failed to list Docker networks: %s", e)
        networks = []
    for network in networks:
        try:
            network_attrs = getattr(network, "attrs", None) or {}
            network_labels = network_attrs.get("Labels") or {}
            if isinstance(network_labels, dict):
                universe_label = network_labels.get("ostorlab.universe")
                if (
                    universe_label == scan_id
                    or universe_label == scan_id_str
                    or str(universe_label) == scan_id_str
                ):
                    logger.debug("Removing network: %s", network_labels)
                    stopped_network.append(network)
                    network.remove()
        except docker_errors.DockerException as e:
            had_errors = True
            logger.warning("Failed to remove network: %s", e)

    try:
        configs = docker_client.configs.list()
    except docker_errors.DockerException as e:
        had_errors = True
        logger.warning("Failed to list Docker configs: %s", e)
        configs = []
    for config in configs:
        try:
            config_attrs = getattr(config, "attrs", None) or {}
            config_spec = (
                config_attrs.get("Spec")
                if isinstance(config_attrs.get("Spec"), dict)
                else {}
            )
            config_labels = (
                config_spec.get("Labels")
                if isinstance(config_spec.get("Labels"), dict)
                else {}
            ) or {}
            universe_label = config_labels.get("ostorlab.universe")
            if (
                universe_label == scan_id
                or universe_label == scan_id_str
                or str(universe_label) == scan_id_str
            ):
                logger.info("Removing config: %s", config_labels)
                stopped_configs.append(config)
                config.remove()
        except docker_errors.DockerException as e:
            had_errors = True
            logger.warning("Failed to remove config: %s", e)

    try:
        volumes = docker_client.volumes.list()
    except (docker_errors.DockerException, KeyError, AttributeError) as e:
        had_errors = True
        logger.warning("Failed to list Docker volumes: %s", e)
        volumes = []
    for volume in volumes:
        try:
            volume_attrs = getattr(volume, "attrs", None) or {}
            volume_name = (
                getattr(volume, "name", None)
                or volume_attrs.get("Name", "")
                or getattr(volume, "id", "")
            )
            volume_labels = volume_attrs.get("Labels") or {}
            universe_label = (
                volume_labels.get("ostorlab.universe")
                if isinstance(volume_labels, dict)
                else None
            )
            if (
                universe_label == scan_id
                or universe_label == scan_id_str
                or str(universe_label) == scan_id_str
                or (
                    volume_name
                    and volume_name
                    in (f"asset_{scan_id_str}", f"{scan_id_str}_mq_data")
                )
            ):
                logger.info("Removing volume: %s", volume_name)
                stopped_volumes.append(volume)
                volume.remove(force=True)
        except (docker_errors.DockerException, KeyError, AttributeError) as e:
            had_errors = True
            logger.warning("Failed to remove volume: %s", e)

    if had_errors is False:
        if stopped_services or stopped_network or stopped_configs or stopped_volumes:
            console.success("All scan components stopped.")
    else:
        logger.warning(
            "Some scan services, networks, configs, or volumes could not be cleaned up for scan %s.",
            scan_id,
        )
    return not had_errors
