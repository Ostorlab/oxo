"""Create Scan via an API Request."""
import json
from typing import Dict, Optional

from ostorlab.apis import request


class CreateAgentScanAPIRequest(request.APIRequest):
    """Persist scan API request."""

    def __init__(self, title: str, asset_id: int, agent_group_id: int) -> None:
        """Initializer"""
        self._title = title
        self.asset_id = asset_id
        self._agent_group_id = agent_group_id


    @property
    def query(self) -> Optional[str]:
        """Sets the query of the API request.

        Returns:
            The query to create the scan.
        """
        return """
            mutation StartAgentScan($scan: AgentScanInputType!){
                createAgentScan(scan: $scan) {
                    scan{
                        id
                    }
                }
            }
        """


    @property
    def data(self) -> Optional[Dict]:
        """Sets the body of the API request.

        Returns:
            The body of the create scan request.
        """
        variables = {
            'scan': {
                'title': self._title,
                'assetId': self.asset_id,
                'agentGroupId': self._agent_group_id
            }
        }
        data = {
            'query': self.query,
            'variables': json.dumps(variables)
        }
        return data
