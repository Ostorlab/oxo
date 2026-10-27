# Graceful worker retirement

A worker selected for shutdown must stop taking new deliveries, finish its current
message, persist its outcome, acknowledge the message, and then exit. Increasing
Docker's grace period alone does not implement that protocol. The SDK must handle
SIGTERM without destroying the active callback's dependencies or acknowledging
unfinished work. Unexpected exceptions and forced process termination still need
broker redelivery and idempotent effects.

## Configure the shutdown deadline

Set `stop_grace_period` in the agent definition (`ostorlab.yaml`), in seconds:

```yaml
kind: Agent
name: risk_worker
in_selectors: []
out_selectors: []
stop_grace_period: 86400
```

The default remains 10 seconds. Fractional seconds are supported, with a minimum
of one nanosecond and a maximum of 9,223,372,036 seconds, keeping the Docker
nanosecond duration within a signed 64-bit integer. Zero, negative, nonfinite,
boolean, null and string values are rejected. The local runtime explicitly sets
`TaskTemplate.ContainerSpec.StopGracePeriod` in nanoseconds when creating a
service. Existing services keep their existing configuration until recreated or
updated through the normal deployment workflow.

Docker sends SIGKILL when the grace period expires. Choose a grace period greater
than the maximum supported active-message duration plus persistence and broker
acknowledgment time. The example allows 24 hours; it cannot guarantee completion
of longer tasks or recovery after host loss. Ensure the container entrypoint
forwards SIGTERM to the worker, or uses exec form so the worker receives it.

## Opt in a verified image

Only after testing the new SDK lifecycle in the actual agent image, add this
Dockerfile label to that image:

```dockerfile
LABEL ostorlab.worker_drain="1"
```

This label declares a tested worker capability. Do not add it automatically to
all builds, copy it onto services as a substitute, or set it on older images.
The autoscaler must inspect the actual deployed image and its effective service
grace period before permitting physical scale-down. An agent definition value or
an aggregate unacknowledged-message count is insufficient evidence. A missing or
unverified capability must leave physical scale-down disabled for busy workers.
Docker may select any replica, so every eligible replica must implement draining.

## Rollout order

1. Ship and test the SDK's cooperative SIGTERM lifecycle. Exercise shutdown while
   idle, during admission, during an active callback, and around persistence and
   acknowledgment. Verify rejected deliveries return to the queue and no new
   callback begins after retirement; test repeated signals and callback errors.
2. Rebuild each agent image with that SDK. Verify its actual entrypoint and
   cleanup hooks with a real broker. Add the capability label only to images
   that pass; pin the deployed image digest.
3. Configure an adequate `stop_grace_period`, deploy the verified image, and
   inspect the effective service specification and the running image identity.
4. Enable the autoscaler capability/grace checks, first in shadow mode and then
   in staging. Test arbitrary victim selection and confirm active work finishes
   before exit. Keep drain resource use in capacity calculations until exit.
5. Enable physical scale-down only after the broker, worker and orchestrator
   checks pass. Revert to deferred physical retirement when verification fails.

Long grace periods delay deployment convergence and shutdown. Drain support does
not make arbitrary external side effects resumable or exactly once. A checkpoint
protocol, durable state, and idempotency require separate implementation and
verification.
