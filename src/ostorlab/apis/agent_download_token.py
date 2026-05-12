"""Request to generate a short-lived Docker registry pull token for an agent image."""

import json
from typing import Dict, Optional, Any

from ostorlab.apis import request


class AgentDownloadTokenAPIRequest(request.APIRequest):
    """Request to generate a download token for a specific agent image."""

    def __init__(self, agent_key: str, version: Optional[str] = None) -> None:
        """Initializer.

        Args:
            agent_key: agent key in the form agent/org/name.
            version: optional version of the agent image.
        """
        self._agent_key = agent_key
        self._version = version

    @property
    def query(self) -> Optional[str]:
        """The mutation to generate a download token for an agent image.

        Returns:
            The mutation to generate a download token.
        """
        return """
            mutation GenerateAgentImageDownloadToken($agentKey: String!, $version: String) {
                generateAgentImageDownloadToken(agentKey: $agentKey, version: $version) {
                    token
                }
            }
        """

    @property
    def data(self) -> Optional[Dict[str, Any]]:
        """Sets the mutation to generate a download token.

        Returns:
            The mutation to generate a download token.
        """
        data = {
            "query": self.query,
            "variables": json.dumps(
                {"agentKey": self._agent_key, "version": self._version}
            ),
        }
        return data
