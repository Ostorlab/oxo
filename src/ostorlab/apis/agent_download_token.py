"""Request to generate a short-lived Docker registry pull token for an agent image."""

from __future__ import annotations

import json
from typing import Any

from ostorlab.apis import request


class AgentDownloadTokenAPIRequest(request.APIRequest):
    """Request to generate a download token for a specific agent image."""

    def __init__(self, agent_key: str, version: str | None = None) -> None:
        """Initializer.

        Args:
            agent_key: agent key in the form agent/org/name.
            version: optional version of the agent image.
        """
        self._agent_key = agent_key
        self._version = version

    @property
    def query(self) -> str | None:
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
    def data(self) -> dict[str, Any]:
        """Generates the request payload containing the query and serialized variables.

        Returns:
            The request payload with the query and variables.
        """
        return {
            "query": self.query,
            "variables": json.dumps(
                {"agentKey": self._agent_key, "version": self._version}
            ),
        }
