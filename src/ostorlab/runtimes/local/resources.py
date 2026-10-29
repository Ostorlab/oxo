"""Hard memory caps and Swarm admission with twenty percent host headroom."""

from __future__ import annotations

import typing

DEFAULT_MEMORY_LIMITS = {
    "agent": 4 * 1024**3,
    "mq": 2 * 1024**3,
    "redis": 512 * 1024**2,
    "jaeger": 512 * 1024**2,
}


def memory_limit(
    service: typing.Literal["agent", "mq", "redis", "jaeger"],
    override: int | None = None,
    definition: int | None = None,
) -> int:
    """Resolve explicit limits before built-in defaults, rejecting unlimited caps."""
    limit = override
    if limit is None:
        limit = definition
    if limit is None:
        limit = DEFAULT_MEMORY_LIMITS[service]
    if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
        raise ValueError(f"{service} memory limit must be a positive integer in bytes")
    return limit


def swarm_resources(limit: int) -> dict[str, typing.Any]:
    """Reserve ceil(limit / 0.8), so admitted hard caps fit within 80% of node RAM."""
    if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
        raise ValueError("Memory limit must be a positive integer in bytes")
    return {
        "Limits": {"MemoryBytes": limit},
        "Reservations": {"MemoryBytes": (limit * 5 + 3) // 4},
        "MemorySwappiness": None,
    }
