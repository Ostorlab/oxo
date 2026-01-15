"""Makes a logout request.

Typical usage example:

logout_request = logout.LogoutAPIRequest()
"""

from typing import Dict, Optional, Any

from ostorlab.apis import request


class LogoutAPIRequest(request.APIRequest):
    """Makes a request to log out the user."""

    @property
    def query(self) -> Optional[str]:
        return """
            mutation Logout {
                logout {
                    message
                }
            }
        """

    @property
    def data(self) -> Optional[Dict[str, Any]]:
        """Gets the user login credentials.

        Returns:
            The user login credentials.
        """
        data = {"query": self.query}
        return data
