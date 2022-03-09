"""Create Agent Group via an API Request."""
import json
from typing import Any, Dict, List, Optional

from ostorlab.apis import request


class CreateAgentGroupAPIRequest(request.APIRequest):
    """Persist agent group API request."""

    def __init__(self, name: str, description: str, agents: List[Dict[str,Any]]) -> None:
        """Initializer"""
        self._name = name
        self._description = description
        self._agents = agents

    @property
    def query(self) -> Optional[str]:
        """Sets the query of the API request.

        Returns:
            The query to create the agent group.
        """
        return """
            query publishAgentGroup($agentGroup: AgentGroupCreateInputType!){
                publishAgentGroup(agentKeys: $agentKeys) {
                    agentGroup{
                        key
                    }
                }
            }
        """


    @property
    def data(self) -> Optional[Dict]:
        """Sets the body of the API request.

        Returns:
            The body of the create agent group request.
        """

        variables = {
            'agentGroup': {
                'name': self._name,
                'description': self._description,
                'access': 'PRIVATE',
                'agents': self._agents
            }
        }
        data = {
            'query': self.query,
            'variables': json.dumps(variables)
        }
        return data
