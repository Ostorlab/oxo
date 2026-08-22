"""Handles API calls to the scanner orchestrator using API key authentication.

Typical usage example:

    scanner_runner = ScannerAPIRunner(api_key="...")
    scanner_runner.execute(request)
"""

import logging
from typing import Any

import httpx

from ostorlab.apis import request as api_request
from ostorlab.apis.runners import runner

SCANNER_GRAPHQL_ENDPOINT = "https://scanner.ostorlab.co/orchestrator/graphql"

logger = logging.getLogger(__name__)


class ScannerAPIRunner(runner.APIRunner):
    """Runner for the scanner orchestrator GraphQL API using API key authentication."""

    def __init__(
        self,
        api_key: str,
        proxy: str | None = None,
        verify: bool = True,
    ) -> None:
        """Constructs all the necessary attributes for the object.

        Args:
            api_key: API key for authentication.
            proxy: The proxy through which a request is made. Defaults to None.
            verify: Whether to verify the TLS certificate. Defaults to True.
        """
        super().__init__(proxy, verify)
        self._api_key = api_key

    @property
    def endpoint(self) -> str:
        """API endpoint."""
        return SCANNER_GRAPHQL_ENDPOINT

    def execute(self, request: api_request.APIRequest) -> dict[str, Any]:
        """Executes a request using the Scanner GraphQL API.

        Args:
            request: The request to be executed

        Raises:
            ResponseError: When the API returns an error

        Returns:
            The API response
        """
        headers = {"X-Api-Key": self._api_key}

        response = self._sent_request(request, headers)
        if response.status_code != 200:
            logger.debug(
                "Response status code is %s: %s",
                response.status_code,
                response.content,
            )
            raise runner.ResponseError(
                f"Response status code is {response.status_code}: {response.content.decode(errors='ignore')}"
            )
        data: dict[str, Any] = response.json()
        errors = data.get("errors")
        if errors is not None and isinstance(errors, list):
            error = errors[0].get("message")
            raise runner.ResponseError(f"Response errors: {error}")
        else:
            return data

    def _sent_request(
        self,
        request: api_request.APIRequest,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Sends an API request to the scanner orchestrator."""
        headers = headers or {}

        with httpx.Client(proxy=self._proxy, verify=self._verify) as client:
            headers["Content-Type"] = "application/json"
            return client.post(
                self.endpoint,
                json=request.data,
                headers=headers,
                timeout=runner.REQUEST_TIMEOUT,
            )
