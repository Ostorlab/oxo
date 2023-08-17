"""Common definition types."""
import dataclasses
from typing import Optional, Union


@dataclasses.dataclass
class Arg:
    """Data class holding a definition.

    The value is always bytes to support all arg values. The type is defined by the type attribute.
    """

    name: str
    type: str
    value: Optional[Union[bytes, int, float, str, bool]] = None
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
