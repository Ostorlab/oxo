"""Handles any configurations related to Ostorlab, such as storing and retriving
    tokens or API keys.

    This module contains code to handle any configurations related to Ostorlab
    such as storing and retriving API keys.
"""

import pathlib

OSTORLAB_PRIVATE_DIR = pathlib.Path.home() / '.ostorlab'


class ConfigurationManager:
    """Handles any configurations related to Ostorlab, such as storing and retriving
       API keys.
    """

    def __init__(self, private_dir: str = OSTORLAB_PRIVATE_DIR):
        """Constructs all the necessary attributes for the object."""
        self._private_dir = private_dir
        self._private_dir.mkdir(parents=True, exist_ok=True)
        self._complete_api_key_path = OSTORLAB_PRIVATE_DIR / 'key'

    def set_api_key(self, api_key: str) -> None:
        """Persists the API key to a file in the given path.

        Args:
            api_key: The authenticated user's generated API key.
        """
        with open(self._complete_api_key_path, 'w', encoding='utf-8') as file:
            file.write(api_key)

    def get_api_key(self) -> str:
        """Gets the API key from the location in which it is saved.

        Returns:
            str: The user's API key.
        """
        with open(self._complete_api_key_path, 'r', encoding='utf-8') as file:
            return file.read()
