"""Search agent from the public api."""

import json
from typing import Dict, Optional

from ostorlab.apis import request

class AgentSearchAPIRequest(request.APIRequest):
    """Search agent from name."""

    def __init__(self, search: str) -> None:
        """Initializer"""
        self._search = search

    @property
    def query(self) -> Optional[str]:
        """The query to fetch the agent details with an agent key.

        Returns:
            The query to fetch the agent details.
        """
        return """
            query Agents($search: String!){
                agents(search: $search) {
                    agents {
                        key
                        name
                        versions {
                            versions {
                                key
                                version
                                description
                            }
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
            'variables': json.dumps({'search': self._search})
        }
        return data
