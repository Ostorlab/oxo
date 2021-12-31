"""Handles any configurations related to Ostorlab, such as storing and retriving
    tokens or API keys.

    This module contains code to handle any configurations related to Ostorlab
    such as storing and retriving API keys.
"""

import pathlib


class ConfigurationManager:
    """Handles any configurations related to Ostorlab, such as storing and retriving
       API keys.
    """

    def __init__(self):
        """Constructs all the necessary attributes for the object.
        """
        self._ostorlab_private_dir = pathlib.Path.home() / '.ostorlab'
        self._ostorlab_private_dir.mkdir(parents=True, exist_ok=True)
        self._complete_api_key_path = self._ostorlab_private_dir / 'key'

    def set_api_key(self, api_key: str) -> None:
        """Persists the API key to a file in the given path

        Args:
            api_key: The authenticated user's generated API key
        """
        with open(self._complete_api_key_path, 'w', encoding='utf-8') as file:
            file.write(api_key)

    def get_api_key(self) -> str:
        """Gets the API key from the location in which it is saved

        Returns:
            str: The user's API key
        """
        with open(self._complete_api_key_path, 'r', encoding='utf-8') as file:
            return file.read()
