"""Handles any configurations related to Ostorlab, such as storing and retrieving tokens or API keys."""

import json
import pathlib
from datetime import datetime
from typing import Dict, Optional, Tuple

OSTORLAB_PRIVATE_DIR = pathlib.Path.home() / ".ostorlab"


class SingletonMeta(type):
    """Metaclass implementation of a singleton pattern."""

    _instances: Dict[object, object] = {}

    def __call__(
        cls: "SingletonMeta", *args: Tuple[object], **kwargs: Dict[object, object]
    ) -> object:
        """Possible changes to the value of the `__init__` argument do not affect the returned instance."""
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class ConfigurationManager(metaclass=SingletonMeta):
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
        self._complete_api_key_path = self._private_dir / "key"
        self._api_key: Optional[str] = None

    @property
    def conf_path(self) -> pathlib.Path:
        """Private configuration path to store scan result, settings and authentication materials."""
        return self._private_dir.resolve()

    @property
    def api_key(self) -> Optional[str]:
        """API key their either uses a predefined value, or retrieve the one in the configuration folder."""
        if self._api_key is not None:
            return self._api_key
        else:
            api_data = self._get_api_data()
            if api_data is not None:
                secret_key: Optional[str] = api_data.get("secret_key")
                return secret_key
            else:
                return None

    @api_key.setter
    def api_key(self, key: Optional[str]) -> None:
        """Set API key"""
        self._api_key = key

    @property
    def api_key_id(self) -> Optional[str]:
        """API key id from the location in which it is saved."""
        if self._api_key is not None:
            return None
        else:
            api_data = self._get_api_data()
            if api_data is not None:
                return api_data.get("api_key_id")
            else:
                return None

    def set_api_data(
        self, secret_key: str, api_key_id: str, expiry_date: Optional[datetime]
    ) -> None:
        """Persists the API data (key, id, expiry date) to a file in the given path.

        Args:
            secret_key: The authenticated user's secret key.
            api_key_id: The authenticated user's generated API key.
            expiry_date: An optional API expiry date.

        Returns:
            None
        """

        api_data = {
            "secret_key": secret_key,
            "api_key_id": api_key_id,
            "expiry_date": expiry_date,
        }

        with open(self._complete_api_key_path, "w", encoding="utf-8") as file:
            data = json.dumps(api_data, indent=4)
            file.write(data)

    def _get_api_data(self) -> Optional[Dict[str, str]]:
        """Gets the API data from the location in which it is saved.

        Returns:
            The user's API data if it exists, otherwise returns None.
        """
        try:
            with open(self._complete_api_key_path, "r", encoding="utf-8") as file:
                api_data: Dict[str, str] = json.loads(file.read())
                return api_data
        except FileNotFoundError:
            return None

    def delete_api_data(self) -> None:
        """Deletes the file containing the API data."""
        self._complete_api_key_path.unlink(missing_ok=True)

    @property
    def is_authenticated(self) -> bool:
        return self.api_key is not None
