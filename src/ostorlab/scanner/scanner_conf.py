"""Representations of the scanner configuration served by the API."""

from __future__ import annotations

import dataclasses
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)
SCAN_RESOURCE_REQUIREMENTS_KEY = "scanResourceRequirements"


@dataclasses.dataclass(frozen=True)
class ScanResourceRequirements:
    """Minimum host resources required to run a scan."""

    cpu_count: int
    memory: int
    disk: int

    @classmethod
    def from_json(cls, value: Any) -> ScanResourceRequirements | None:
        """Create scan resource requirements from a JSON-compatible value."""
        if isinstance(value, dict) is False:
            return None

        resource_values = (
            value.get("cpuCount"),
            value.get("memory"),
            value.get("disk"),
        )
        if any(
            isinstance(resource_value, int) is False
            or isinstance(resource_value, bool) is True
            or resource_value < 0
            for resource_value in resource_values
        ):
            return None

        return cls(
            cpu_count=resource_values[0],
            memory=resource_values[1],
            disk=resource_values[2],
        )


@dataclasses.dataclass
class ScannerConfig:
    """Represents the configuration for a scanner."""

    scan_resource_requirements: dict[str, ScanResourceRequirements]
    api_key: str | None = None

    @classmethod
    def from_json(cls, config: dict[str, Any]) -> ScannerConfig | None:
        """Creates a ScannerConfig instance from a JSON configuration.

        Args:
            config: The JSON configuration.

        Returns:
            ScannerConfig: An instance of ScannerConfig.
        """

        data = config.get("data") or {}
        scanners_data = data.get("scanners") or {}
        subject_configs = scanners_data.get("scanners") or []

        if len(subject_configs) == 0:
            return None

        conf = subject_configs[0].get("config") or {}
        resource_requirements = {}
        raw_resource_requirements = conf.get(SCAN_RESOURCE_REQUIREMENTS_KEY, {})
        if isinstance(raw_resource_requirements, str):
            try:
                raw_resource_requirements = json.loads(raw_resource_requirements)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON in scanResourceRequirements")
                raw_resource_requirements = {}
        if isinstance(raw_resource_requirements, dict):
            for scan_type, requirements in raw_resource_requirements.items():
                parsed_requirements = ScanResourceRequirements.from_json(requirements)
                if isinstance(scan_type, str) and parsed_requirements is not None:
                    resource_requirements[scan_type] = parsed_requirements
                else:
                    logger.warning(
                        "Skipping malformed scan resource requirements entry: %r",
                        scan_type,
                    )
        elif SCAN_RESOURCE_REQUIREMENTS_KEY in conf:
            logger.warning(
                "scanResourceRequirements must be an object, received %s",
                type(raw_resource_requirements).__name__,
            )
        return cls(
            scan_resource_requirements=resource_requirements,
            api_key=conf.get("apiKey"),
        )
