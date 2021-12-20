from typing import Dict, Optional

from . import request


class UsernamePasswordLoginAPIRequest(request.APIRequest):

    def __init__(self, username: str, password: str) -> None:
        self._username = username
        self._password = password

    @property
    def endpoint(self):
        return request.TOKEN_ENDPOINT

    @property
    def query(self) -> Optional[str]:
        return None

    @property
    def data(self) -> Optional[Dict]:
        data = {
            'username': self._username,
            'password': self._password,
        }
        return data
