"""Get agent details from the public api."""

import json
from typing import Any

from ostorlab.apis import request


class AgentDetailsAPIRequest(request.APIRequest):
    """Get agent details for a specified agent_key."""

    def __init__(
        self,
        agent_key: str,
        use_experimental: bool = False,
        channel: str | None = None,
    ) -> None:
        """Initializer"""
        self._agent_key = agent_key
        self._use_experimental = use_experimental
        self._channel = channel

    @property
    def query(self) -> str:
        """The query to fetch the agent details with an agent key.

        The `channel` argument is only declared when a channel is set, since store
        servers that predate release channels reject it even when it is null.

        Returns:
            The query to fetch the agent details.
        """
        channel_variable = ""
        channel_argument = ""
        if self._channel is not None:
            channel_variable = ", $channel: String"
            channel_argument = ", channel: $channel"
        return f"""
            query Agent($agentKey: String!, $useExperimental: Boolean{channel_variable}){{
                agent(agentKey: $agentKey) {{
                    name,
                    gitLocation,
                    yamlFileLocation,
                    dockerLocation,
                    access,
                    listable,
                    key
                    versions(orderBy: Version, sort: Desc, page: 1, numberElements: 1, useExperimental: $useExperimental{channel_argument}) {{
                      versions {{
                        version
                      }}
                    }}
                }}
            }}
        """

    @property
    def data(self) -> dict[str, Any]:
        """Sets the body of the API request, to fetch the specific agent.

        Returns:
            The body of the agent details request.
        """
        variables: dict[str, Any] = {
            "agentKey": self._agent_key,
            "useExperimental": self._use_experimental,
        }
        if self._channel is not None:
            variables["channel"] = self._channel
        return {"query": self.query, "variables": json.dumps(variables)}
