"""Revokes the API key."""

from typing import Dict, Optional
import json
import logging

from ostorlab.apis import request


logger = logging.getLogger(__name__)


class RevokeAPIKeyAPIRequest(request.APIRequest):
    """Revokes the API key."""

    def __init__(self, api_key_id: str):
        """Sets API key identifier.

        Args:
           api_key_id: The API key id used to revoke the API key.
        """
        self._api_key_id = api_key_id

    @property
    def query(self) -> Optional[str]:
        """Defines the query to revoke the API key.

        Returns:
            The query to revoke the API key
        """
        return """
         mutation RevokeApiKey($apiKeyId: String!) {
               revokeApiKey(apiKeyId: $apiKeyId) {
                  result
               }
            }
        """

    @property
    def data(self) -> Optional[Dict]:
        """Sets the query and variables to revoke the API key.

        Returns:
              The query and variables to revoke the API key.
        """
        data = {
            'query': self.query,
            'variables': json.dumps({'apiKeyId': self._api_key_id})
        }
        return data
