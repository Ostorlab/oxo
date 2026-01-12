"""Handles any configurations related to Ostorlab, such as storing and retrieving tokens or API keys."""

import json
import pathlib
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
        self._uploads_dir = private_dir / "uploads"
        self._uploads_dir.mkdir(parents=True, exist_ok=True)
        self._complete_authorization_token_path = self._private_dir / "token"
        self._api_key: Optional[str] = None

    @property
    def conf_path(self) -> pathlib.Path:
        """Private configuration path to store scan result, settings and authentication materials."""
        return self._private_dir.resolve()

    @property
    def upload_path(self) -> pathlib.Path:
        """Private path to store uploaded assets."""
        return self._uploads_dir.resolve()

    @property
    def api_key(self) -> Optional[str]:
        """API key their either uses a predefined value, or retrieve the one in the configuration folder."""
        if self._api_key is not None:
            return self._api_key

    @property
    def authorization_token(self) -> Optional[str]:
        """retrieve authorization token in the configuration folder."""
        authorization_token_data = self._get_authorization_token()
        if authorization_token_data is not None:
            authorization_token: Optional[str] = authorization_token_data.get(
                "authorization_token"
            )
            return authorization_token
        else:
            return None

    @api_key.setter
    def api_key(self, key: Optional[str]) -> None:
        """Set API key"""
        self._api_key = key

    def set_authorization_token(self, authorization_token: str) -> None:
        """Persists the Authorization token to a file in the given path.

        Args:
            authorization_token: Token to be used as a request header for to authorize authenticated user.

        Returns:
            None
        """

        authorization_token_data = {"authorization_token": authorization_token}

        with open(
            self._complete_authorization_token_path, "w", encoding="utf-8"
        ) as file:
            data = json.dumps(authorization_token_data, indent=4)
            file.write(data)

    def _get_authorization_token(self) -> Optional[Dict[str, str]]:
        """Gets the authorization token from the location in which it is saved.

        Returns:
            The user's authorization token if it exists, otherwise returns None.
        """
        try:
            with open(
                self._complete_authorization_token_path, "r", encoding="utf-8"
            ) as file:
                authorization_token_data: Dict[str, str] = json.loads(file.read())
                return authorization_token_data
        except FileNotFoundError:
            return None

    def delete_authorization_token_data(self) -> None:
        """Deletes the file containing the API data."""
        self._complete_authorization_token_path.unlink(missing_ok=True)

    @property
    def is_authenticated(self) -> bool:
        return self.api_key is not None or self.authorization_token is not None
