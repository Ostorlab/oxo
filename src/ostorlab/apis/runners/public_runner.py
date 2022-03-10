"""Handles the public API calls.

    Typical usage example:
    public_runner = PublicAPIRunner()
    public_runner.execute()
"""

from typing import Dict

import requests

from ostorlab.apis import request as api_request
from ostorlab.apis.runners import runner

PUBLIC_GRAPHQL_ENDPOINT = 'https://api.ostorlab.co/apis/public_graphql'


class PublicAPIRunner(runner.APIRunner):
    """Responsible for the public API calls, and preparing the responses."""

    @property
    def endpoint(self) -> str:
        """API endpoint."""
        return PUBLIC_GRAPHQL_ENDPOINT

    def execute(self, request: api_request.APIRequest) -> Dict:
        """Executes a request using the Public GraphQL API.

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

    def _sent_request(self, request: api_request.APIRequest) -> requests.Response:
        """Sends an API request."""
        if self._proxy is not None:
            proxy = {
                'https': self._proxy
            }
        else:
            proxy = None
        return requests.post(self.endpoint, data=request.data,
                             proxies=proxy, verify=self._verify)
