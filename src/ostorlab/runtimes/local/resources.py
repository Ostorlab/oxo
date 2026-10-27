"""Hard memory caps and Swarm admission with twenty percent host headroom."""

from __future__ import annotations

import os
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
    """Resolve explicit limits before environment defaults, rejecting unlimited caps."""
    limit = override
    if limit is None:
        limit = definition
    if limit is None:
        environment = f"OSTORLAB_{service.upper()}_MEMORY_LIMIT_BYTES"
        configured = os.environ.get(environment)
        if configured is None:
            limit = DEFAULT_MEMORY_LIMITS[service]
        else:
            try:
                limit = int(configured)
            except ValueError as error:
                raise ValueError(
                    f"{environment} must be a positive integer in bytes"
                ) from error
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
