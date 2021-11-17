import logging
from typing import Dict

import requests

from . import login
from . import request as api_request

logger = logging.getLogger(__name__)


class Error(Exception):
    """Base Error Class"""


class AuthenticationError(Error):
    """Authentication Error."""


class ResponseError(Error):
    """Response Error."""


class Runner:

    def __init__(self, username: str, password: str, proxy: str = None, verify: bool = True):
        self._username = username
        self._password = password
        self._proxy = proxy
        self._verify = verify
        self._token = None

    def authenticate(self):
        login_request = login.UsernamePasswordLoginAPIRequest(self._username, self._password)
        response = self._sent_request(login_request)
        if response.status_code != 200:
            logger.debug(response.content)
            raise AuthenticationError()
        else:
            self._token = response.json().get('token')

    def execute(self, request: api_request.APIRequest) -> Dict:
        response = self._sent_request(request, headers={'Authorization': f'Token {self._token}'}, multipart=True)
        if response.status_code != 200:
            raise ResponseError(f'Response status code is {response.status_code}: {response.content}')
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
