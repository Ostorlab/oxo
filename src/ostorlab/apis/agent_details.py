"""Get agent details from the public api."""

import json
from typing import Any

from ostorlab.apis import request


class AgentDetailsAPIRequest(request.APIRequest):
    """Get agent details for a specified agent_key."""

    def __init__(self, agent_key: str, use_experimental: bool = False) -> None:
        """Initializer"""
        self._agent_key = agent_key
        self._use_experimental = use_experimental

    @property
    def query(self) -> str:
        """The query to fetch the agent details with an agent key.

        Returns:
            The query to fetch the agent details.
        """
        return """
            query Agent($agentKey: String!, $useExperimental: Boolean){
                agent(agentKey: $agentKey) {
                    name,
                    gitLocation,
                    yamlFileLocation,
                    dockerLocation,
                    access,
                    listable,
                    key
                    versions(orderBy: Version, sort: Desc, page: 1, numberElements: 1, useExperimental: $useExperimental) {
                      versions {
                        version
                      }
                    }
                }
            }
        """

    @property
    def data(self) -> dict[str, Any]:
        """Sets the body of the API request, to fetch the specific agent.

        Returns:
            The body of the agent details request.
        """
        return {
            "query": self.query,
            "variables": json.dumps(
                {"agentKey": self._agent_key, "useExperimental": self._use_experimental}
            ),
        }
