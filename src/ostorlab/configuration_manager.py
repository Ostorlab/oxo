"""Handles any configurations related to Ostorlab, such as storing and retrieving tokens or API keys."""

import json
import pathlib
from datetime import datetime
from typing import Dict, Optional

OSTORLAB_PRIVATE_DIR = pathlib.Path.home() / '.ostorlab'


class ConfigurationManager:
    """Handles any configurations related to Ostorlab, such as storing and retrieving
       API keys.
    """

    def __init__(self, private_dir: pathlib.Path = OSTORLAB_PRIVATE_DIR):
        """Constructs all the necessary attributes for the object
        Args:
            private_dir: The private directory where Ostorlab configurations are stored.
            Defaults to OSTORLAB_PRIVATE_DIR.
        """
        self._private_dir = private_dir
        self._private_dir.mkdir(parents=True, exist_ok=True)
        self._complete_api_key_path = self._private_dir / 'key'


    @property
    def conf_path(self) -> pathlib.Path:
        return self._private_dir.resolve()

    def set_api_data(self, secret_key: str, api_key_id: str, expiry_date: Optional[datetime]) -> None:
        """Persists the API data (key, id, expiry date) to a file in the given path.

        Args:
            api_key: The authenticated user's generated API key.
        """

        api_data = {
            'secret_key': secret_key,
            'api_key_id': api_key_id,
            'expiry_date': expiry_date
        }

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
            return api_data.get('secret_key')
        else:
            return None

    def get_api_key_id(self) -> Optional[str]:
        """Gets the API key id from the location in which it is saved.

        Returns:
            The user's API key id if it exists, otherwise returns None.
        """
        api_data = self.get_api_data()
        if api_data is not None:
            return api_data.get('api_key_id')
        else:
            return None

    def get_api_key_expiry_date(self) -> Optional[datetime]:
        """Gets the API key expiry date from the location in which it is saved.

        Returns:
            The user's API key expiry date if it exists, otherwise returns None.
        """
        api_data = self.get_api_data()
        if api_data is not None:
            return api_data.get('expiry_date')
        else:
            return None

    def delete_api_data(self) -> None:
        """Deletes the file containing the API data."""
        self._complete_api_key_path.unlink(missing_ok=True)

    @property
    def is_authenticated(self):
        return self.get_api_key_id() is not None
