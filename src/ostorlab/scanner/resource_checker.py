"""Host resource checks for on-premise scans."""

import logging
import pathlib

import psutil

from ostorlab.scanner import scanner_conf

logger = logging.getLogger(__name__)


def can_run_scan(
    scan_key: str,
    requirements: dict[str, scanner_conf.ScanResourceRequirements],
    disk_path: str | None = None,
) -> bool:
    """Return whether the host has resources for ``scan_key`` at ``disk_path``."""
    if disk_path is None:
        disk_path = pathlib.Path.cwd().anchor

    scan_requirements = (
        requirements.get(scan_key)
        or requirements.get(scan_key.split("/")[-1])
        or requirements.get("default")
    )
    if scan_requirements is None:
        logger.warning("No resource requirements configured for scan %s", scan_key)
        return False

    try:
        cpu_count = psutil.cpu_count(logical=True)
        total_memory = psutil.virtual_memory().total
        available_disk = psutil.disk_usage(disk_path).free
    except (OSError, psutil.Error) as error:
        logger.warning("Unable to determine host resources for %s: %s", scan_key, error)
        return False
    if cpu_count is None:
        logger.warning("Unable to determine host CPU count for %s", scan_key)
        return False
    has_capacity = (
        cpu_count >= scan_requirements.cpu_count
        and total_memory >= scan_requirements.memory
        and available_disk >= scan_requirements.disk
    )
    if has_capacity is False:
        logger.warning(
            "Insufficient resources for %s: host cpu=%d total_memory=%d "
            "free_disk=%d; "
            "required cpu=%d memory=%d disk=%d",
            scan_key,
            cpu_count,
            total_memory,
            available_disk,
            scan_requirements.cpu_count,
            scan_requirements.memory,
            scan_requirements.disk,
        )
    return has_capacity
