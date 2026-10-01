"""Handles any configurations related to Ostorlab, such as storing and retrieving tokens or API keys."""

import json
import os
import pathlib
from typing import ClassVar
from typing import Optional

OSTORLAB_PRIVATE_DIR = pathlib.Path.home() / ".ostorlab"


class SingletonMeta(type):
    """Cache configuration managers by their resolved private directory."""

    _instances: ClassVar[
        dict[tuple["SingletonMeta", pathlib.Path], "ConfigurationManager"]
    ] = {}

    def __call__(
        cls: "SingletonMeta", private_dir: Optional[pathlib.Path] = None
    ) -> "ConfigurationManager":
        """Share credential state only between callers using the same directory."""
        if private_dir is None:
            environment_dir = os.environ.get("OSTORLAB_PRIVATE_DIR")
            private_dir = (
                OSTORLAB_PRIVATE_DIR
                if environment_dir is None or environment_dir == ""
                else pathlib.Path(environment_dir)
            )
        resolved_dir = private_dir.expanduser().resolve()
        cache_key = (cls, resolved_dir)
        if cache_key not in cls._instances:
            cls._instances[cache_key] = super().__call__(private_dir=resolved_dir)
        return cls._instances[cache_key]


class ConfigurationManager(metaclass=SingletonMeta):
    """Handles any configurations related to Ostorlab, such as storing and retrieving
    API keys.
    """

    def __init__(self, private_dir: pathlib.Path = OSTORLAB_PRIVATE_DIR) -> None:
        """Constructs all the necessary attributes for the object
        Args:
            private_dir: The private directory where Ostorlab configurations are stored.
            Defaults to OSTORLAB_PRIVATE_DIR, or the environment override of that name.
        """
        self._private_dir = private_dir
        self._private_dir.mkdir(parents=True, exist_ok=True)
        self._uploads_dir = private_dir / "uploads"
        self._uploads_dir.mkdir(parents=True, exist_ok=True)
        self._complete_authorization_token_path = self._private_dir / "token"
        self._api_key: str | None = None

    @property
    def conf_path(self) -> pathlib.Path:
        """Private configuration path to store scan result, settings and authentication materials."""
        return self._private_dir.resolve()

    @property
    def upload_path(self) -> pathlib.Path:
        """Private path to store uploaded assets."""
        return self._uploads_dir.resolve()

    @property
    def api_key(self) -> str | None:
        """API key their either uses a predefined value, or retrieve the one in the configuration folder."""
        if self._api_key is not None:
            return self._api_key
        return None

    @api_key.setter
    def api_key(self, key: str | None) -> None:
        """Set API key"""
        self._api_key = key

    @property
    def authorization_token(self) -> str | None:
        """retrieve authorization token in the configuration folder."""
        authorization_token_data = self._get_authorization_token()
        if authorization_token_data is not None:
            authorization_token: str | None = authorization_token_data.get(
                "authorization_token"
            )
            return authorization_token
        else:
            return None

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

    def _get_authorization_token(self) -> dict[str, str] | None:
        """Gets the authorization token from the location in which it is saved.

        Returns:
            The user's authorization token if it exists, otherwise returns None.
        """
        try:
            with open(
                self._complete_authorization_token_path, "r", encoding="utf-8"
            ) as file:
                authorization_token_data: dict[str, str] = json.loads(file.read())
                return authorization_token_data
        except FileNotFoundError:
            return None

    def delete_authorization_token_data(self) -> None:
        """Deletes the file containing the API data."""
        self._complete_authorization_token_path.unlink(missing_ok=True)

    @property
    def is_authenticated(self) -> bool:
        return self.api_key is not None or self.authorization_token is not None
