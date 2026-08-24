"""Helper module for cleaning up Docker resources belonging to a scan universe."""

import logging
from collections.abc import Callable
from typing import Any

import tenacity
from docker import errors as docker_errors

from ostorlab.cli import console as cli_console

logger = logging.getLogger(__name__)
console = cli_console.Console()


@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_fixed(0.2),
    retry=tenacity.retry_if_exception_type(
        (docker_errors.DockerException, docker_errors.APIError)
    ),
    reraise=True,
)
def _remove_resource_with_retry(resource: Any) -> None:
    """Removes a Docker resource with retry on transient errors, ignoring NotFound."""
    try:
        resource.remove()
    except docker_errors.NotFound:
        pass


def _extract_labels(resource: Any) -> dict[str, Any]:
    """Extract labels from resource attributes."""
    attrs = getattr(resource, "attrs", None) or {}
    if not isinstance(attrs, dict):
        return {}
    spec = attrs.get("Spec")
    if isinstance(spec, dict):
        labels = spec.get("Labels")
        if isinstance(labels, dict):
            return labels
    labels = attrs.get("Labels")
    if isinstance(labels, dict):
        return labels
    return {}


def _extract_name(resource: Any) -> str:
    """Extract display name or ID from resource."""
    attrs = getattr(resource, "attrs", None) or {}
    if isinstance(attrs, dict):
        spec = attrs.get("Spec")
        if isinstance(spec, dict) and spec.get("Name"):
            return str(spec["Name"])
        if attrs.get("Name"):
            return str(attrs["Name"])
        if attrs.get("ID"):
            return str(attrs["ID"])
        if attrs.get("Id"):
            return str(attrs["Id"])
    try:
        name = getattr(resource, "name", None)
        if name:
            return str(name)
    except Exception:
        pass
    try:
        res_id = getattr(resource, "id", None)
        if res_id:
            return str(res_id)
    except Exception:
        pass
    return ""


def _cleanup_resource_collection(
    collection: Any,
    resource_type: str,
    scan_id_str: str,
    scan_id: int | str | None = None,
    extra_items: list[Any] | None = None,
    extra_matcher: Callable[[Any], bool] | None = None,
) -> tuple[list[Any], bool]:
    """Lists, filters, and removes Docker resources belonging to universe.

    Returns:
        tuple[list[Any], bool]: (stopped_resources, had_errors)
    """
    if collection is None:
        return [], False

    stopped = []
    had_errors = False
    items: list[Any] = []

    try:
        items = list(
            collection.list(filters={"label": f"ostorlab.universe={scan_id_str}"})
        )
    except (
        docker_errors.DockerException,
        docker_errors.APIError,
        KeyError,
        AttributeError,
    ) as e:
        had_errors = True
        logger.warning("Failed to list Docker %ss: %s", resource_type, e)

    if extra_items:
        for item in extra_items:
            if item not in items:
                items.append(item)

    for item in items:
        try:
            labels = _extract_labels(item)
            universe_label = labels.get("ostorlab.universe")
            is_match = (
                universe_label == scan_id
                or universe_label == scan_id_str
                or str(universe_label) == scan_id_str
                or (extra_matcher is not None and extra_matcher(item))
            )
            if is_match:
                item_name = _extract_name(item)
                logger.info("Removing %s: %s", resource_type, item_name)
                stopped.append(item)
                _remove_resource_with_retry(item)
        except (
            docker_errors.DockerException,
            docker_errors.APIError,
            KeyError,
            AttributeError,
        ) as e:
            had_errors = True
            logger.warning("Failed to remove %s: %s", resource_type, e)

    return stopped, had_errors


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

    scan_id_str = str(scan_id).strip()
    logger.info("Cleaning up scan resources for universe %s", scan_id_str)
    had_errors = False
    stopped_components: list[Any] = []

    stopped, err = _cleanup_resource_collection(
        collection=getattr(docker_client, "services", None),
        resource_type="service",
        scan_id_str=scan_id_str,
        scan_id=scan_id,
    )
    stopped_components.extend(stopped)
    had_errors = had_errors or err

    stopped, err = _cleanup_resource_collection(
        collection=getattr(docker_client, "networks", None),
        resource_type="network",
        scan_id_str=scan_id_str,
        scan_id=scan_id,
    )
    stopped_components.extend(stopped)
    had_errors = had_errors or err

    stopped, err = _cleanup_resource_collection(
        collection=getattr(docker_client, "configs", None),
        resource_type="config",
        scan_id_str=scan_id_str,
        scan_id=scan_id,
    )
    stopped_components.extend(stopped)
    had_errors = had_errors or err

    named_volumes = []
    named_volume_targets = (f"asset_{scan_id_str}", f"{scan_id_str}_mq_data")
    vol_collection = getattr(docker_client, "volumes", None)
    if vol_collection is not None:
        vol_getter = getattr(vol_collection, "get", None)
        if callable(vol_getter):
            for named_vol in named_volume_targets:
                try:
                    vol = vol_getter(named_vol)
                    if vol is not None:
                        named_volumes.append(vol)
                except docker_errors.NotFound:
                    pass
                except (docker_errors.DockerException, docker_errors.APIError) as e:
                    had_errors = True
                    logger.warning("Failed to get named volume %s: %s", named_vol, e)

    def _volume_name_matcher(vol: Any) -> bool:
        vol_name = _extract_name(vol)
        return vol_name in named_volume_targets

    stopped, err = _cleanup_resource_collection(
        collection=vol_collection,
        resource_type="volume",
        scan_id_str=scan_id_str,
        scan_id=scan_id,
        extra_items=named_volumes,
        extra_matcher=_volume_name_matcher,
    )
    stopped_components.extend(stopped)
    had_errors = had_errors or err

    if had_errors is False:
        if stopped_components:
            console.success("All scan components stopped.")
    else:
        logger.warning(
            "Some scan services, networks, configs, or volumes could not be cleaned up for scan %s.",
            scan_id,
        )
    return not had_errors
