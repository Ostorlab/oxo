"""Common definition types."""

import dataclasses
import json
from typing import Optional, Union, Any


@dataclasses.dataclass
class Arg:
    """Data class holding a definition of an argument for an agent.
    The actual type of value will be determined using the type attribute.
    The type could be one of the following: string, number, int, boolean, array, or object."""

    name: str
    type: str
    value: Optional[Union[bytes, int, float, str, bool]] = None
    description: Optional[str] = None

    @classmethod
    def from_values(
        cls,
        name: str,
        type: str,
        value: Optional[Union[bytes, int, float, str, bool]] = None,
        description: Optional[str] = None,
    ) -> "Arg":
        if isinstance(value, bytes):
            if type == "binary":
                value = value
            # When the value comes from a message received in the NATS.
            else:
                value = Arg.parse_value_string(
                    value_str=value.decode(), actual_type=type
                )

        # When the value comes from the CLI arguments using --arg.
        elif isinstance(value, str):
            value = Arg.parse_value_string(value_str=value, actual_type=type)

        # When the value comes from the CLI with a YAML file for the group definition.
        else:
            # In this case, we don't need to parse the value since it will already be in the correct type.
            pass

        return cls(name, type, value, description)

    @staticmethod
    def parse_value_string(actual_type: str, value_str: str) -> Any:
        if actual_type == "string":
            return value_str
        elif actual_type == "number":
            return float(value_str)
        elif actual_type == "int":
            return int(value_str)
        elif actual_type == "boolean":
            return value_str.lower() == "true"
        elif actual_type in ("array", "object"):
            return json.loads(value_str)
        else:
            raise ValueError(f"Unsupported argument type: {actual_type}")


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
