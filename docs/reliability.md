# Worker reliability and memory admission

Failed worker messages are retried and then retained in a durable `.failed` queue
instead of being silently acknowledged. Memory limits and Swarm reservations
bound workloads. Automatic worker recovery is disabled by default: enable it only
after the tracker, backend and cleanup handlers support retained failures.

## How is memory reserved for scan services?

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

## How does message delivery survive worker failures?

Ordinary publications are persistent and require publisher confirmation. Outputs
with no bound consumer remain optional: the broker may discard an unrouted
publication without failing the producer. A confirmation alone does not establish
that an ordinary output was routed or processed.

Consumers acknowledge after processing succeeds, or after the broker confirms a
persistent replacement in the same worker queue. Processing failures are retried
with a bounded attempt count and backoff, then transferred to the durable
`<queue>.failed` queue. These transfers require both confirmation and routing
(`mandatory=True`); a failed transfer requeues the original delivery. Backoff
also applies after processing attempts are exhausted, so an unavailable failed
queue cannot cause a tight redelivery loop.

A lost connection or worker crash leaves unacknowledged deliveries available for
redelivery. The retry count bounds caught processing failures. A process killed
before publishing its replacement can redeliver repeatedly without advancing
that count.

**At-least-once delivery:** side effects may repeat, so handlers must tolerate
redelivery. Broker confirmation followed by a disconnect before ACK can leave
both copies available. The at-least-once delivery behavior described here does
not restore cooperative shutdown draining.

Broker persistence does not protect messages from an external cleanup handler.
The lifecycle requirements below apply even with automatic recovery disabled.

## How does the scanner recover stalled workers?

**Automatic recovery is opt-in.** Only `OSTORLAB_WORKER_RECOVERY_ENABLED=1` in the
scanner process enables it. An unset variable or any other value disables recovery
queries, worker restarts and recovery-triggered scan-state changes. Memory limits
and SDK message handling operate independently of this setting.

When enabled, the scanner checks active scans every 60 seconds, including while
at capacity. It fetches all pages from the scanner API and fails closed on errors
or incomplete pagination. Matching universe and container ownership labels are
required. Paused, stopped, inactive, shared, one-shot and zero-replica services
are excluded. A replica count deliberately set to zero, for example by an
operator or autoscaler policy, is left at zero and is not treated as a stall.
State for workers that disappear or become ineligible is pruned.

**A worker is stalled when its queue has ready messages without consumers, or it
has no running replicas despite a positive desired count.** Healthy consumers
are not restarted merely because work remains queued or processing takes time.

A stall must persist through a 120-second observation grace period. Recovery
reloads the service and refreshes active scan state before each action; it does
not reuse an earlier snapshot to decide whether a paused scan can be restarted.

Recovery forces a worker service update without changing its replica count.
Attempts and last-attempt time are stored on the service's root labels. At most
two attempts are allowed, with a 120-second cooldown, across scanner restarts.

Exhausted recovery or a nonempty failed queue logs task status and requests scan
progress `error`. Once the API confirms success, that scan is not reported again
while it remains in the active local snapshot. Failed or unconfirmed updates are
retried on a later reconciliation cycle. This deduplication resets on scanner
restart or after the scan leaves the active local snapshot.

If RabbitMQ cannot be queried, reconciliation logs the failure and skips that
scan. It does not restart brokers or recover sustained broker outages.

## How to roll out worker reliability changes

**An external cleanup handler can still delete the broker, and the existing
tracker can overwrite `error` with `done`. Keep automatic recovery disabled until
those companion services preserve terminal failures and retained brokers.**

Startup health checks fail when required services cannot become healthy. The
startup-error path cleans up the attempted universe, including its broker
resources. A failed snapshot restore retains the remote snapshot as the recovery
source.

Before enabling recovery:

- Update the tracker and backend so terminal errors cannot become successful scans.
- Configure stop/cleanup handlers to retain failed queues and broker volumes for
  inspection and replay. The scanner does not purge queues or provide automatic
  replay. This is also required before relying on SDK failed-message retention.
- Ensure the autoscaler preserves reservations and deliberate zero replicas.
- Rebuild worker images with the updated SDK; updating the scanner alone does not
  change message handling in running workers.
- Validate representative memory limits in staging, recreate services, then set
  `OSTORLAB_WORKER_RECOVERY_ENABLED=1` on the scanner process and restart it.

Use these commands during rollout:

```sh
docker service ps --no-trunc SERVICE
docker exec MQ_CONTAINER rabbitmqctl list_queues name messages_ready messages_unacknowledged consumers
docker exec MQ_CONTAINER rabbitmq-diagnostics alarms
journalctl -k --grep='Out of memory|Killed process|oom-kill'
```

Inspect `.failed` queue counts, pending tasks, RabbitMQ memory alarms and node OOM
logs. Replace `SERVICE` and `MQ_CONTAINER` with the affected service and broker
container names; run the journal command on the Docker host.

The API update has no compare-and-set progress condition. A scan can change state
between the final active-state read and the error mutation. Closing that race
requires a scanner endpoint change; the fresh read only narrows the window.
