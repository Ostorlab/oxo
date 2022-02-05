"""Handles the creation of an API key."""

from ostorlab.apis import request
from datetime import datetime
from typing import Dict, Optional
import json
import logging

logger = logging.getLogger(__name__)


class CreateAPIKeyAPIRequest(request.APIRequest):
    """Handles the creation of an API key."""

    def __init__(self, expiry_date: Optional[datetime] = None):
        """Constructs all the necessary attributes for the object.

        Args:
           expiry_date: The date when the API key should expire. Defaults to None.
        """
        self._name = 'Ostorlab CLI'
        self._expiry_date = expiry_date

    @property
    def query(self) -> Optional[str]:
        """Defines the query to generate an API key.

        Returns:
            The query to generate an API key
        """
        return """
         mutation CreateApiKey($name: String!, $expiryDate: DateTime) {
               createApiKey(name: $name, expiryDate: $expiryDate) {
                  apiKey {
                     secretKey
                     apiKey {
                        expiryDate
                        id
                     }
                  }
               }
            }
        """

    @property
    def data(self) -> Optional[Dict]:
        """Sets the query and variables to generate an API key.

        Returns:
              The API key, name, and expiry date.
        """
        data = {
            'query': self.query,
            'variables': json.dumps({'name': self._name,
                                        'expiryDate': self._expiry_date
                                        })
        }
        return data
