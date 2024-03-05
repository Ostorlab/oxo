"""Common definition types."""

import dataclasses
from typing import Optional, Union


@dataclasses.dataclass
class Arg:
    """Data class holding a definition of an argument for an agent.
    the actual type of value will be determined using type attribute.
    type could be one of the following: string, number, boolean, array, object"""

    name: str
    type: str
    value: Optional[Union[bytes, int, float, str, bool, list[str]]] = None
    description: Optional[str] = None


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
