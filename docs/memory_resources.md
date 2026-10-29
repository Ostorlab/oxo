# Memory limits and reservations

Every new local Swarm service has a hard memory limit. Agent group `mem_limit`
overrides the image's `mem_limit`; otherwise the scanner process environment
sets the default. Values are positive integer bytes. Zero, negative values and
booleans are rejected.

| Service | Default hard limit | Environment override |
| --- | --- | --- |
| Agent replica | 4 GiB | `OSTORLAB_AGENT_MEMORY_LIMIT_BYTES` |
| RabbitMQ | 2 GiB | `OSTORLAB_MQ_MEMORY_LIMIT_BYTES` |
| Redis | 512 MiB | `OSTORLAB_REDIS_MEMORY_LIMIT_BYTES` |
| Jaeger | 512 MiB | `OSTORLAB_JAEGER_MEMORY_LIMIT_BYTES` |

Each replica reserves `ceil(hard_limit / 0.8)` bytes in Swarm. OXO hard limits
therefore total at most 80% of each node's schedulable RAM, including replicas
added by an autoscaler. **Reservations are admission accounting, not additional
usable container memory.** They do not account for unrelated processes or
containers without reservations. No CPU reservation or CPU limit is configured.

When capacity is insufficient, tasks remain pending. Inspect
`docker service ps --no-trunc SERVICE` for the scheduler's reason.

Existing services must be recreated to acquire these resources. Changing the
scanner environment does not edit them. The 4 GiB agent default is a fallback,
not a measured requirement: size memory-heavy agents explicitly before rollout.

RabbitMQ's absolute memory watermark is half its hard limit. Its fixed hostname
and persistent data volume are retained; backpressure can occur before the hard
limit.
