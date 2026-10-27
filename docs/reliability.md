# Worker reliability and memory admission

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

Each replica reserves `ceil(hard_limit / 0.8)` bytes in Swarm. Consequently,
Swarm admits OXO hard limits totaling at most 80% of each node's schedulable RAM,
including replicas added later by an autoscaler. Reservations are admission
accounting, not additional usable container memory. Tasks remain pending when
capacity is insufficient; inspect `docker service ps --no-trunc SERVICE` for the
scheduler's reason. This does not account for unrelated processes or containers
without reservations. Existing services must be recreated in a controlled rollout
to acquire these resources; changing the scanner environment does not edit them.
Startup health checks fail when required services cannot become healthy. The
existing startup-error path cleans up the attempted universe, including its local
broker resources; this differs from ongoing recovery of an active scan. For a
failed snapshot restore, the remote snapshot remains the recovery source.

The 4 GiB agent default is a fallback, not a measured requirement for every agent.
Set explicit limits for memory-heavy agents before rollout and provision nodes
large enough for their reservations and supporting services. RabbitMQ's absolute
memory watermark is half its hard limit; its fixed hostname and persistent data
volume are retained. Backpressure can therefore occur before the container limit.
A deliberate agent replica count of zero stays zero.

## Message delivery

Publications are persistent and require publisher confirmation and a matching
queue (`mandatory=True`). A successful publish means the broker accepted routing;
it does not mean a consumer completed processing. Publish-before-subscribe flows
and optional outputs with no bound queue now fail explicitly: deploy consumers
and their bindings before producers, or adapt optional output flows deliberately.

Consumers acknowledge only after processing succeeds. Processing failures are
republished with a bounded attempt count and backoff, then transferred to the
persistent `<queue>.failed` queue on exhaustion. The original delivery is
acknowledged only after confirmation of that transfer. A lost connection or a
worker crash leaves unacknowledged deliveries available for redelivery. The retry
count bounds caught processing failures; a process killed before the replacement
is durably published can redeliver repeatedly without advancing that count. This is
at-least-once delivery: side effects may repeat, so agents should use idempotency
where required. A publication or transfer failure is surfaced instead of being
silently acknowledged.

## Scanner recovery

The production scanner checks active scans every 60 seconds, including while it
is at its concurrent scan limit. It fetches all pages from the scanner API and
fails closed on errors or incomplete pagination. Only services with matching
universe and container scan ownership labels are eligible. Paused, stopped,
inactive, shared, one-shot and zero-replica services are excluded.

A worker is stalled when its queue has ready messages without consumers, or it
has no running replicas despite a positive desired count. Both conditions must
persist through a 120-second observation grace period. Healthy consumers are not
restarted merely because work remains queued or processing takes a long time.
Recovery reloads the service and rechecks active scan state before action. It
forces a worker service update without changing its replica count. Attempts and
last-attempt time are stored on the service's root labels; two attempts with a
120-second cooldown are allowed across scanner process restarts.

Exhausted recovery or a nonempty terminal failure queue produces an actionable
error log including task status, and requests scan progress `error` only after a
fresh active-state check. OXO recovery never purges queues, recreates RabbitMQ,
removes services or deletes broker volumes. Retain the broker for inspection and
replay; automatic replay of terminal failures is not provided.

## Coordinated rollout

Deploy the updated agent package in worker images as well as the updated scanner;
updating scanner code alone does not change running worker message handling.
Validate representative agent limits and queue bindings in staging before replacing
services. Monitor pending tasks, OOM exits, RabbitMQ memory alarms and `.failed`
queue depth.

The external autoscaler, cloud tracker and stop/cleanup handlers live in separate
repositories and are not changed here. They must preserve resource reservations
and deliberate zero replica counts, avoid overwriting an explicit `error` with
`done`, and retain failed queues and broker volumes long enough for diagnosis.
In particular, an external cleanup handler triggered by `error` can still delete
the broker: configure retention there before enabling this recovery rollout.
The API's update mutation has no compare-and-set progress condition; a scan can
change state between the final active-state read and the error mutation. Closing
that remaining race requires a scanner endpoint change.
