"""Handles all authenticated API calls and behind the scenes operations such as authentication, validation, etc.

Typical usage example:

authenticated_runner = AuthenticatedAPIRunner(username, password, token_duration)
authenticated_runner.authenticate()
"""

import datetime
import logging
from typing import Dict, Optional, Any

import click
import httpx
import ubjson
import json

from ostorlab.apis import create_api_key
from ostorlab.apis import request as api_request
from ostorlab.apis.runners import login_runner
from ostorlab.apis.runners import runner
from ostorlab.cli import console as cli_console

AUTHENTICATED_GRAPHQL_ENDPOINT = "https://api.ostorlab.co/apis/graphql"


logger = logging.getLogger(__name__)
console = cli_console.Console()


class AuthenticationError(runner.Error):
    """Authentication Error."""


class AuthenticatedAPIRunner(runner.APIRunner):
    """Handles all authenticated API calls and behind the scenes operations such as authentication,
    validation, etc.
    """

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        token_duration: Optional[datetime.datetime] = None,
        proxy: Optional[str] = None,
        verify: bool = True,
        api_key: Optional[str] = None,
    ):
        """Constructs all the necessary attributes for the object.

        Args:
            username: the username (email) used to log in to use the token based authentication.
            password: the password used to log in to use the token based authentication.
            token_duration: The duration for which the token is valid
            (Can be in minutes, hours, days, or a combination of any two or all three).
            proxy: The proxy through which a request is made. Defaults to None.
            verify: Whether to verify the TLS certificate. Defaults to True.
            api_key: Use API KEY based authentication. Used if token is not defined.
        """
        super().__init__(proxy, verify)
        self._username = username
        self._password = password
        self._token_duration = token_duration
        self._api_key = api_key or self._configuration_manager.api_key
        self._token: Optional[str] = None
        self._otp_token: Optional[str] = None

    @property
    def endpoint(self) -> str:
        """API endpoint."""
        return AUTHENTICATED_GRAPHQL_ENDPOINT

    def authenticate(self) -> None:
        """Authenticates the user.

        Raises:
            AuthenticationError: If user credentials are not valid.
        """
        with console.status("Logging into your account"):
            login_api_runner = login_runner.LoginAPIRunner(
                username=self._username,
                password=self._password,
                otp_token=self._otp_token,
                proxy=self._proxy,
                verify=self._verify,
            )
            response = login_api_runner.login_user()

        if response.status_code != 200:
            field_errors = response.json().get("non_field_errors")
            if (
                field_errors is not None
                and field_errors[0] == 'Must include "otp_token"'
            ):
                self._otp_token = click.prompt(
                    "Please enter the OTP code from your authenticator app"
                )
                self.authenticate()
            else:
                logger.debug("response %s", response.content)
                raise AuthenticationError(response.status_code)
        else:
            self._token = response.json().get("token")
            with console.status("Generating API key"):
                api_key_response = self.execute(
                    create_api_key.CreateAPIKeyAPIRequest(self._token_duration)
                )
                console.success("API key generated")

            api_data = api_key_response["data"]["createApiKey"]["apiKey"]
            secret_key = api_data["secretKey"]
            api_key_id = api_data["apiKey"]["id"]
            expiry_date = api_data["apiKey"]["expiryDate"]

            self._api_key = secret_key
            with console.status("Persisting API key"):
                self._configuration_manager.set_api_data(
                    secret_key, api_key_id, expiry_date
                )
                console.success("API key persisted")
            self._token = None
            console.success(":white_check_mark: Authentication successful")

    def unauthenticate(self) -> None:
        self._api_key = None

    def execute(self, request: api_request.APIRequest) -> Dict[str, Any]:
        """Executes a request using the Authenticated GraphQL API.

        Args:
            request: The request to be executed

        Raises:
            ResponseError: When the API returns an error

        Returns:
            The API response
        """
        if self._token is not None:
            headers = {"Authorization": f"Token {self._token}"}
        elif self._api_key is not None:
            headers = {"X-Api-Key": f"{self._api_key}"}
        else:
            headers = None
            console.warning("No authentication credentials were provided.")

        response = self._sent_request(request, headers)
        if response.status_code != 200:
            logger.debug(
                "Response status code is %s: %s", response.status_code, response.content
            )
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
                timeout=runner.REQUEST_TIMEOUT,
            )

    def execute_ubjson_request(self, request: api_request.APIRequest) -> Dict[str, Any]:
        """Executes a request using the Authenticated GraphQL API.

        Args:
            request: The request to be executed

        Raises:
            ResponseError: When the API returns an error

        Returns:
            The API response
        """
        if self._token is not None:
            headers = {"Authorization": f"Token {self._token}"}
        elif self._api_key is not None:
            headers = {"X-Api-Key": f"{self._api_key}"}
        else:
            headers = None
            console.warning("No authentication credentials were provided.")

        if headers is not None:
            headers |= {"Content-type": "application/ubjson"}

        response = self._send_ubjson_request(request, headers)
        if response.status_code != 200:
            logger.debug(
                "Response status code is %s: %s", response.status_code, response.content
            )
            raise runner.ResponseError(
                f'Response status code is {response.status_code}: {response.content.decode(errors="ignore")}'
            )
        data: Dict[str, Any] = json.loads(response.content.decode())
        errors = data.get("errors")
        if errors is not None and isinstance(errors, list):
            error = errors[0].get("message")
            raise runner.ResponseError(f"Response errors: {error}")
        else:
            return data

    def _send_ubjson_request(
        self, request: api_request.APIRequest, headers: Optional[Dict[str, str]] = None
    ) -> httpx.Response:
        """Sends an API request."""
        with httpx.Client(proxy=self._proxy, verify=self._verify) as client:
            return client.post(
                self.endpoint,
                data=ubjson.dumpb(request.data),
                files=request.files,
                headers=headers,
                timeout=runner.REQUEST_TIMEOUT,
            )
