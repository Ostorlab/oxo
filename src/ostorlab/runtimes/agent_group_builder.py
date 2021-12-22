import io
from ostorlab.runtimes.runtime import AgentGroupDefinition


class AgentGroupBuilder:
    def build(self, file: io.FileIO) -> AgentGroupDefinition:
        """build AgentDefinition instance from agentKey"""

        return AgentGroupDefinition()
