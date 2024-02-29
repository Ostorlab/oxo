"""Handles calls to the token API.

Typical usage example:
public_runner = LoginAPIRunner(username, password, otp_token)
public_runner.login_user()
"""

import httpx
from typing import Dict, Optional, Any

from ostorlab.apis.runners import runner
from ostorlab.apis import request as api_request
from ostorlab.apis import login


TOKEN_ENDPOINT = "https://api.ostorlab.co/apis/token/"


class LoginAPIRunner(runner.APIRunner):
    """Responsible for the public API calls, and preparing the responses."""

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        otp_token: Optional[str] = None,
        proxy: Optional[str] = None,
        verify: bool = True,
    ):
        """Constructs all the necessary attributes for the object.

        Args:
            username: the username (email) used to log in.
            password: the password used to log in.
            proxy: The proxy through which a request is made. Defaults to None.
            verify: Whether to verify the TLS certificate. Defaults to True.
        """
        super().__init__(proxy, verify)
        self._username = username
        self._password = password
        self._otp_token = otp_token

    @property
    def endpoint(self) -> str:
        """Token API endpoint."""
        return TOKEN_ENDPOINT

    def login_user(self) -> httpx.Response:
        """Logs in the user.

        Returns:
            The API response.
        """
        if self._username is None or self._password is None:
            raise ValueError("Missing credentials.")

        login_request = login.UsernamePasswordLoginAPIRequest(
            self._username, self._password, self._otp_token
        )

        return self._sent_request(login_request)

    def execute(self, request: api_request.APIRequest) -> Dict[str, Any]:
        """Executes a request using the Token GraphQL API.

        Args:
            request: The request to be executed

        Raises:
            ResponseError: When the API returns an error

        Returns:
            The API response
        """
        response = self._sent_request(request)
        if response.status_code != 200:
            raise runner.ResponseError(
                f'Response status code is {response.status_code}: {response.content.decode(errors="ignore")}'
            )
        data: Dict[str, Any] = response.json()
        errors = data.get("errors")
        if errors is not None and isinstance(errors, list):
            error = errors[0].get("message")
            raise runner.ResponseError(f"Response errors: {error}")
        else:
            return data
