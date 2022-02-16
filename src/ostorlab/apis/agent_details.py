"""Get agent details from the public api."""

import json
from typing import Dict, Optional

from ostorlab.apis import request

class AgentDetailsAPIRequest(request.APIRequest):
    """Get agent details for a specified agent_key."""

    def __init__(self, agent_key: str) -> None:
        """Initializer"""
        self._agent_key = agent_key

    @property
    def query(self) -> Optional[str]:
        """The query to fetch the agent details with an agent key.

        Returns:
            The query to fetch the agent details.
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
                    versions(orderBy: Version, sort: Desc, page: 1, numberElements: 1) {
                      versions {
                        version
                      }
                    }
                }
            }
        """

    @property
    def data(self) -> Optional[Dict]:
        """Sets the body of the API request, to fetch the specific agent.

        Returns:
            The body of the agent details request.
        """
        data = {
            'query': self.query,
            'variables': json.dumps({'agentKey': self._agent_key})
        }
        return data
