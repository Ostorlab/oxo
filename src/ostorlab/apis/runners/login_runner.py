"""Handles calls to the token API.

    Typical usage example:
    public_runner = LoginAPIRunner(username, password, otp_token)
    public_runner.login_user()
"""

import requests
from typing import Dict, Optional

from ostorlab.apis.runners import runner
from ostorlab.apis import request as api_request
from ostorlab.apis import login



TOKEN_ENDPOINT = 'https://api.ostorlab.co/apis/token/'


class LoginAPIRunner(runner.APIRunner):
    """Responsible for the public API calls, and preparing the responses."""
    def __init__(self,
                 username: str = None,
                 password: str = None,
                 otp_token: Optional[str] = None,
                 proxy: str = None,
                 verify: bool = True
                 ):
        """Constructs all the necessary attributes for the object.

        Args:
            username: the username (email) used to login.
            password: the password used to login.
            proxy: The proxy through which a request is made. Defaults to None.
            verify: Whether or not to verify the TLS certificate. Defaults to True.
        """
        super().__init__(proxy, verify)
        self._username = username
        self._password = password
        self._otp_token = otp_token

    @property
    def endpoint(self) -> str:
        """Token API endpoint."""
        return TOKEN_ENDPOINT

    def login_user(self) -> requests.models.Response:
        """Logs in the user.

        Returns:
            The API response.
        """
        login_request = login.UsernamePasswordLoginAPIRequest(self._username,
                                                              self._password,
                                                              self._otp_token)

        return self._sent_request(login_request)


    def execute(self, request: api_request.APIRequest) -> Dict:
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
                f'Response status code is {response.status_code}: {response.content}')
        data = response.json()
        if data.get('errors') is not None:
            error = data.get('errors')[0]['message']
            raise runner.ResponseError(f'Response errors: {error}')
        else:
            return data
