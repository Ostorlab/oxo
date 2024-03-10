"""Common definition types."""

import dataclasses
import json
from typing import Optional, Union, Any


@dataclasses.dataclass
class Arg:
    """Data class holding a definition of an argument for an agent.
    The actual type of value will be determined using the type attribute.
    The type could be one of the following: string, number, boolean, binary array, or object."""

    name: str
    type: str
    value: Optional[Union[bytes, int, float, str, bool]] = None
    description: Optional[str] = None

    @classmethod
    def build(
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
                value = Arg.convert_str(value_str=value.decode(), target_type=type)

        # When the value comes from the CLI arguments using --arg.
        elif isinstance(value, str):
            value = Arg.convert_str(value_str=value, target_type=type)

        # When the value comes from the CLI with a YAML file for the group definition.
        else:
            # In this case, we don't need to parse the value since it will already be in the correct type.
            pass

        return cls(name, type, value, description)

    @staticmethod
    def convert_str(value_str: str, target_type: str) -> Any:
        """
        Convert a string value to the specified type.

        Args:
            target_type: The desired data type to convert the value to.

            value_str: The string representation of the value.

        Returns:
            Any: The converted value of the specified type.

        Raises:
            ValueError: If the target_type is not supported or If the value_str cannot be converted to the specified type.
        """
        if target_type == "string":
            return value_str
        elif target_type == "int":
            return int(value_str)
        elif target_type == "number":
            return float(value_str)
        elif target_type == "boolean":
            return value_str.lower() == "true"
        elif target_type == "array":
            try:
                return json.loads(value_str)
            except ValueError:
                return value_str.split(",")
        elif target_type == "object":
            return json.loads(value_str)
        else:
            raise ValueError(f"Unsupported argument type: {target_type}")


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
