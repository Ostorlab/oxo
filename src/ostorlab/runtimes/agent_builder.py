from ostorlab.runtimes.runtime import AgentDefinition


class AgentBuilder:

    def build(self, agent_key: str) -> AgentDefinition:
        """build AgentDefinition instance from agentKey"""
        # build AgentDefinition from agent_key logic
        return AgentDefinition(name='agent', path='path', container_image='')
