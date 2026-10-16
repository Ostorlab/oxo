"""Handles API calls to the scanner orchestrator using API key authentication.

Typical usage example:

    scanner_runner = ScannerAPIRunner(api_key="...")
    scanner_runner.execute(request)
"""

import logging
from typing import Any
from typing import Optional
from typing import cast

import httpx
import tenacity
from tenacity.wait import WaitBaseT

from ostorlab.apis import request as api_request
from ostorlab.apis.runners import runner

SCANNER_GRAPHQL_ENDPOINT = "https://scanner.ostorlab.co/orchestrator/graphql"

SCANNER_REQUEST_ATTEMPTS = 3
SCANNER_RETRY_WAIT = tenacity.wait_exponential(multiplier=1, min=1, max=30)

_TRANSIENT_HTTP_ERRORS = (
    httpx.NetworkError,
    httpx.TimeoutException,
    httpx.ProxyError,
    httpx.RemoteProtocolError,
)

logger = logging.getLogger(__name__)


def _is_transient_server_error(response: httpx.Response) -> bool:
    """Returns whether the orchestrator answered with a transient server error.

    Server errors (5xx) are temporary: the load balancer or the orchestrator may
    be briefly unavailable and the same request can succeed on retry.
    """
    return response.is_server_error


def _last_response(retry_state: tenacity.RetryCallState) -> httpx.Response:
    """Returns the last orchestrator response once the retry budget is exhausted."""
    outcome = retry_state.outcome
    if outcome is None:
        raise RuntimeError("Retry state has no outcome.")
    return cast(httpx.Response, outcome.result())


class ScannerAPIRunner(runner.APIRunner):
    """Runner for the scanner orchestrator GraphQL API using API key authentication."""

    def __init__(
        self,
        api_key: Optional[str],
        proxy: str | None = None,
        verify: bool = True,
        retry_wait: WaitBaseT | None = None,
    ) -> None:
        """Constructs all the necessary attributes for the object.

        Args:
            api_key: API key for authentication.
            proxy: The proxy through which a request is made. Defaults to None.
            verify: Whether to verify the TLS certificate. Defaults to True.
            retry_wait: Backoff strategy between retries of transient failures.
                Defaults to an exponential backoff capped at 30 seconds.
        """
        super().__init__(proxy, verify)
        self._api_key = api_key
        self._retry_wait: WaitBaseT
        if retry_wait is None:
            self._retry_wait = SCANNER_RETRY_WAIT
        else:
            self._retry_wait = retry_wait

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

        if request.is_mutation is True:
            response = self._sent_request(request, headers)
        else:
            response = self._sent_request_with_retry(request, headers)
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

    def _sent_request_with_retry(
        self,
        request: api_request.APIRequest,
        headers: dict[str, str] | dict[str, str | None] | None = None,
    ) -> httpx.Response:
        """Sends a read-only request, retrying transient server and transport failures."""
        retrying = tenacity.Retrying(
            stop=tenacity.stop_after_attempt(SCANNER_REQUEST_ATTEMPTS),
            wait=self._retry_wait,
            retry=tenacity.retry_any(
                tenacity.retry_if_result(_is_transient_server_error),
                tenacity.retry_if_exception_type(_TRANSIENT_HTTP_ERRORS),
            ),
            retry_error_callback=_last_response,
        )
        return retrying(self._sent_request, request, headers)

    def _sent_request(
        self,
        request: api_request.APIRequest,
        headers: dict[str, str] | dict[str, str | None] | None = None,
    ) -> httpx.Response:
        """Sends an API request to the scanner orchestrator."""
        headers = headers or {}

        with httpx.Client(proxy=self._proxy, verify=self._verify) as client:
            headers["Content-Type"] = "application/json"
            return client.post(
                self.endpoint,
                json=request.data,
                headers=cast(dict[str, str], headers),
                timeout=runner.REQUEST_TIMEOUT,
            )
