"""Get agent details from the public api."""

import json
from typing import Dict, Optional, Any

from ostorlab.apis import request


class AgentDetailsAPIRequest(request.APIRequest):
    """Get agent details for a specified agent_key."""

    def __init__(
        self, agent_key: str, reporting_scan_id: Optional[int] = None
    ) -> None:
        """Initializer"""
        self._agent_key = agent_key
        self._reporting_scan_id = reporting_scan_id

    @property
    def query(self) -> Optional[str]:
        """The query to fetch the agent details with an agent key.

        Returns:
            The query to fetch the agent details.
        """
        return """
            query Agent($agentKey: String!, $reportingScanId: Int){
                agent(agentKey: $agentKey) {
                    name,
                    gitLocation,
                    yamlFileLocation,
                    dockerLocation,
                    access,
                    listable,
                    key
                    versions(orderBy: Version, sort: Desc, page: 1, numberElements: 1, reportingScanId: $reportingScanId) {
                      versions {
                        version
                      }
                    }
                }
            }
        """

    @property
    def data(self) -> Optional[Dict[str, Any]]:
        """Sets the body of the API request, to fetch the specific agent.

        Returns:
            The body of the agent details request.
        """
        variables: Dict[str, Any] = {"agentKey": self._agent_key}
        if self._reporting_scan_id is not None:
            variables["reportingScanId"] = self._reporting_scan_id
        data = {
            "query": self.query,
            "variables": json.dumps(variables),
        }
        return data
