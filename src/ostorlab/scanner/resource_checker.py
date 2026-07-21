"""Host resource checks for on-premise scans."""

import logging

import psutil

from ostorlab.scanner import scanner_conf


logger = logging.getLogger(__name__)


def can_run_scan(
    scan_key: str,
    requirements: dict[str, scanner_conf.ScanResourceRequirements],
) -> bool:
    """Return whether the host has the resources required by ``scan_key``."""
    scan_requirements = requirements.get(scan_key)
    if scan_requirements is None:
        scan_requirements = requirements.get(scan_key.split("/")[-1])
    if scan_requirements is None:
        scan_requirements = requirements.get("default")
    if scan_requirements is None:
        logger.warning("No resource requirements configured for scan %s", scan_key)
        return False

    cpu_count = psutil.cpu_count(logical=True) or 0
    available_memory = psutil.virtual_memory().available
    available_disk = psutil.disk_usage("/").free
    has_capacity = (
        cpu_count >= scan_requirements.cpu_count
        and available_memory >= scan_requirements.memory
        and available_disk >= scan_requirements.disk
    )
    if has_capacity is False:
        logger.warning(
            "Insufficient resources for %s: available cpu=%d memory=%d disk=%d; "
            "required cpu=%d memory=%d disk=%d",
            scan_key,
            cpu_count,
            available_memory,
            available_disk,
            scan_requirements.cpu_count,
            scan_requirements.memory,
            scan_requirements.disk,
        )
    return has_capacity
