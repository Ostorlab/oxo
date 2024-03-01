"""API runner base class.
API runners for example : Public API Runner, Authenticated API Runner, inherit from the base class
to access the different features.
This module also has classes for authentication errors, API response errors, etc"""

import abc
from typing import Dict, Optional, Any

import httpx

from ostorlab import configuration_manager as config_manager
from ostorlab.apis import request as api_request

REQUEST_TIMEOUT = 80


class Error(Exception):
    """Base Error Class"""


class ResponseError(Error):
    """Response Error."""


class APIRunner(abc.ABC):
    """Handles API calls and behind the scenes operations."""

    def __init__(self, proxy: Optional[str] = None, verify: bool = True):
        """Constructs the necessary attributes for the object.

        Args:
            proxy: The proxy through which a request is made. Defaults to None.
            verify: Whether to verify the TLS certificate. Defaults to True.
        """
        self._proxy = proxy
        self._verify = verify
        self._configuration_manager: config_manager.ConfigurationManager = (
            config_manager.ConfigurationManager()
        )

    @property
    def endpoint(self) -> str:
        """API endpoint."""
        raise NotImplementedError("Missing implementation")

    @abc.abstractmethod
    def execute(self, request: api_request.APIRequest) -> Dict[str, Any]:
        """Executes a request using the GraphQL API.

        Args:
            request: The request to be executed

        Raises:
            ResponseError: When the API returns an error

        Returns:
            The API response
        """
        raise NotImplementedError("Missing implementation")

    def _sent_request(
        self, request: api_request.APIRequest, headers: Optional[Dict[str, str]] = None
    ) -> httpx.Response:
        """Sends an API request."""
        with httpx.Client(proxy=self._proxy, verify=self._verify) as client:
            return client.post(
                self.endpoint,
                data=request.data,
                files=request.files,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )
