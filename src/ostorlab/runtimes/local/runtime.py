from ostorlab.assets import Asset
from ostorlab.runtimes import runtime
from ostorlab.runtimes.runtime import AgentRunDefinition


class LocalRuntime(runtime.Runtime):
    """Local runtime runes agents locally using Docker Swarm.
    Local runtime starts a Vanilla RabbitMQ service, starts all the agents listed in the `AgentRunDefinition`, checks
    their status and then inject the target asset.
    """

    def can_run(self, agent_run_definition: AgentRunDefinition) -> bool:
        raise NotImplementedError()

    def scan(self, agent_run_definition: AgentRunDefinition, asset: Asset) -> None:
        raise NotImplementedError()
