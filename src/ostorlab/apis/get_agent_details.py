"""Get agent details from the public api."""

import json
from typing import Dict, Optional

from ostorlab.apis import request

class AgentAPIRequest(request.APIRequest):
    """Get agent details for a specified agent_key."""

    def __init__(self, agent_key: str) -> None:
        """Initializer"""
        self.agent_key = agent_key

    @property
    def query(self) -> Optional[str]:
        """Defines the query to fetch agent details from agent key.

        Returns:
            The query fetch agent details.
        """
        return """
            query Agent($agentKey: String!){
                agent(agentKey: $agentKey) {
                    name,
                    gitLocation,
                    yamlFileLocation,
                    dockerLocation,
                    access,
                    listable,
                    key
                }
            }
        """

    @property
    def endpoint(self) -> str:
        return request.PUBLIC_GRAPHQL_ENDPOINT

    @property
    def data(self) -> Optional[Dict]:
        """Sets the query to fetch the specific agent.

        Returns:
              The query to agent details.
        """
        data = {
            'query': self.query,
            'variables': json.dumps({'agentKey': self.agent_key})
        }
        return data
