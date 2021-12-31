"""Handles any configurations related to Ostorlab, such as storing and retriving
    tokens or API keys.

    This module contains code to handle any configurations related to Ostorlab
    such as storing and retriving API keys.
"""

from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import json


class ConfigurationManager:
    """Handles any configurations related to Ostorlab, such as storing and retriving
       API keys.
    """

    def __init__(self):
        """Constructs all the necessary attributes for the object.
        """
        self._ostorlab_private_dir = Path.home() / '.ostorlab'
        self._ostorlab_private_dir.mkdir(parents=True, exist_ok=True)
        self._complete_api_key_path = self._ostorlab_private_dir / 'key'

    def set_api_data(self, api_data: Dict) -> None:
        """Persists the API data (key, id, expiry date) to a file in the given path.

        Args:
            api_key: The authenticated user's generated API key.
        """
        with open(self._complete_api_key_path, 'w', encoding='utf-8') as file:
            data = json.dumps(api_data, indent=4)
            file.write(data)

    def get_api_data(self) -> Optional[Dict]:
        """Gets the API data from the location in which it is saved.

        Returns:
            The user's API data if it exists, otherwise returns None.
        """
        try:
            with open(self._complete_api_key_path, 'r', encoding='utf-8') as file:
                # TODO (Rabson): Handle case where file content is not a dict
                return json.loads(file.read())
        except FileNotFoundError:
            return None

    def get_api_key(self) -> Optional[str]:
        """Gets the API key from the location in which it is saved.

        Returns:
            The user's API key if it exists, otherwise returns None.
        """
        api_data = self.get_api_data()
        if api_data is not None:
            return api_data.get('secretKey')
        else:
            return None

    def get_api_key_id(self) -> Optional[str]:
        """Gets the API key id from the location in which it is saved.

        Returns:
            The user's API key id if it exists, otherwise returns None.
        """
        api_data = self.get_api_data()
        if api_data is not None and api_data.get('apiKey') is not None:
            return api_data.get('apiKey').get('id')
        else:
            return None

    def get_api_key_expiry_date(self) -> Optional[datetime]:
        """Gets the API key expiry date from the location in which it is saved.

        Returns:
            The user's API key expiry date if it exists, otherwise returns None.
        """
        api_data = self.get_api_data()
        if api_data is not None and api_data.get('apiKey') is not None:
            return api_data.get('apiKey').get('expiryDate')
        else:
            return None


    def delete_api_data(self) -> None:
        """Deletes the file containing the API data.
        """
        # TODO handle exception
        self._complete_api_key_path.unlink(missing_ok=True)
