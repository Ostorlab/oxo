"""Common definition types."""

import dataclasses


@dataclasses.dataclass
class Arg:
    """Data class holding a definition of an argument for an agent.
    the actual type of value will be determined using type attribute.
    type could be one of the following: string, number, boolean, array, object"""

    name: str
    type: str
    value: bytes | int | float | str | bool | list[str] | None = None
    description: str | None = None


@dataclasses.dataclass
class PortMapping:
    """Data class defining a port mapping source to destination"""

    source_port: int
    destination_port: int


@dataclasses.dataclass
class ScannerState:
    """Current scanner state."""

    scanner_id: str
    scan_id: int | None
    cpu_load: float
    memory_load: float
    total_cpu: int
    total_memory: int
    hostname: str
    ip: str
