"""Common definition types."""

import dataclasses
import json
from typing import Optional, Union


@dataclasses.dataclass
class Arg:
    """Data class holding a definition of an argument for an agent.
    The actual type of value will be determined using the type attribute.
    The type could be one of the following: string, number, int, boolean, array, or object."""

    name: str
    type: str
    value: Optional[Union[bytes, int, float, str, bool]] = None
    description: Optional[str] = None

    def __post_init__(self) -> None:
        if isinstance(self.value, bytes):
            if self.type == "binary":
                self.value = self.value
            # When the value comes from a message received in the NATS.
            else:
                self._parse_value_string(self.value.decode())

        # When the value comes from the CLI arguments using --arg.
        elif isinstance(self.value, str):
            self._parse_value_string(self.value)

        # When the value comes from the CLI with a YAML file for the group definition.
        else:
            # In this case, we don't need to parse the value since it will already be in the correct type.
            pass

    def _parse_value_string(self, value_str: str) -> None:
        if self.type == "string":
            self.value = value_str
        elif self.type == "number":
            self.value = float(value_str)
        elif self.type == "int":
            self.value = int(value_str)
        elif self.type == "boolean":
            self.value = value_str.lower() == "true"
        elif self.type in ("array", "object"):
            self.value = json.loads(value_str)
        else:
            raise ValueError(f"Unsupported argument type: {self.type}")


@dataclasses.dataclass
class PortMapping:
    """Data class defining a port mapping source to destination"""

    source_port: int
    destination_port: int


@dataclasses.dataclass
class ScannerState:
    """Current scanner state."""

    scanner_id: str
    scan_id: Optional[int]
    cpu_load: float
    memory_load: float
    total_cpu: int
    total_memory: int
    hostname: str
    ip: str
