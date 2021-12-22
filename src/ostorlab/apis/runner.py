import logging
from typing import Dict, Optional

import requests
import click

from . import login
from . import request as api_request

logger = logging.getLogger(__name__)


class Error(Exception):
    """Base Error Class"""


class AuthenticationError(Error):
    """Authentication Error."""


class ResponseError(Error):
    """Response Error."""


class APIRunner:

    def __init__(self, username: Optional[str], password: Optional[str], expires: Optional[str], proxy: str = None, verify: bool = True):
        self._username = username
        self._password = password
        self._proxy = proxy
        self._verify = verify
        self._token = None
        self._expires = expires
        self._otp_token = None

    def create_request(self):
        if self._otp_token is not None:
            login_request = login.UsernamePasswordLoginAPIRequest(
                self._username, self._password, self._otp_token)
        else:
            login_request = login.UsernamePasswordLoginAPIRequest(
                self._username, self._password)
        return self._sent_request(login_request)

    def authenticate(self):
        response = self.create_request()

        if response.status_code != 200:
            field_errors = response.json().get('non_field_errors')

            if field_errors is not None:
                if field_errors[0] == "Must include \"otp_token\"":
                    self._otp_token = click.prompt(
                        'Please enter the OTP code from your authenticator app')
                    self.authenticate()
                else:
                    logger.debug(response.content)
                    raise AuthenticationError(response.status_code)
        else:
            self._token = response.json().get('token')

    def execute(self, request: api_request.APIRequest) -> Dict:
        response = self._sent_request(
            request, headers={'Authorization': f'Token {self._token}'}, multipart=True)
        if response.status_code != 200:
            raise ResponseError(
                f'Response status code is {response.status_code}: {response.content}')
        else:
            return response.json()

    def _sent_request(self, request: api_request.APIRequest, headers=None, multipart=False) -> requests.Response:
        if self._proxy is not None:
            proxy = {
                'https': self._proxy
            }
        else:
            proxy = None

        if multipart:
            return requests.post(request.endpoint, files=request.data, headers=headers, proxies=proxy,
                                 verify=self._verify)
        else:
            return requests.post(request.endpoint, data=request.data, headers=headers, proxies=proxy,
                                 verify=self._verify)
