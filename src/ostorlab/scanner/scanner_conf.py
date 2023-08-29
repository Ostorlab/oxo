"""Representations of nats configuration definitions."""

import dataclasses
from typing import List, Dict, Any


@dataclasses.dataclass
class RegistryConfig:
    """Represents the configuration for container registry credentials."""

    username: str
    token: str
    url: str


@dataclasses.dataclass
class SubjectBusConfigs:
    """Represents the configuration for a subject and its corresponding queue."""

    subject: str
    queue: str


@dataclasses.dataclass
class ScannerConfig:
    """Represents the configuration for a scanner."""

    bus_url: str
    bus_cluster_id: str
    bus_client_name: str
    registry_conf: RegistryConfig
    subject_bus_configs: List[SubjectBusConfigs]

    @classmethod
    def from_json(cls, config: Dict[str, Any]):
        """Creates a ScannerConfig instance from a JSON configuration.

        Args:
            config: The JSON configuration.

        Returns:
            ScannerConfig: An instance of ScannerConfig.
        """

        subject_configs = config.get("data", {}).get("scanners", {}).get("scanners", [])

        if len(subject_configs) == 0:
            return None

        subject_configs = subject_configs[0].get("config", {})
        bus_configs = []
        for subject_config in subject_configs.get("subjectBusConfigs", {}).get(
            "subjectBusConfigs", []
        ):
            bus_configs.append(
                SubjectBusConfigs(
                    subject=subject_config.get("subject"),
                    queue=subject_config.get("queue"),
                )
            )
        conf = (
            config.get("data", {})
            .get("scanners", {})
            .get("scanners", [])[0]
            .get("config", {})
        )
        registry_conf = conf.get("registryConfiguration", {})
        registry_conf_instance = RegistryConfig(
            username=registry_conf.get("accountName"),
            token=registry_conf.get("credentials"),
            url=registry_conf.get("url"),
        )
        return cls(
            bus_url=conf.get("busUrl"),
            bus_cluster_id=conf.get("busClusterId"),
            bus_client_name=conf.get("busClientName"),
            registry_conf=registry_conf_instance,
            subject_bus_configs=bus_configs,
        )
