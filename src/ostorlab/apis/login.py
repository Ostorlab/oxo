from typing import Dict, Optional

from . import request


class UsernamePasswordLoginAPIRequest(request.APIRequest):  

    def __init__(self, username: str, password: str, otp_token: Optional[str] = None) -> None:
        self._username = username
        self._password = password
        self._otp_token = otp_token

    @property
    def endpoint(self):
        return request.TOKEN_ENDPOINT

    @property
    def query(self) -> Optional[str]:
        return None

    @property
    def data(self) -> Optional[Dict]:
        """Gets the user login credentials

        Returns:
            Optional[Dict]: The user login credentials
        """        
        if self._otp_token is not None:
            data = {
                'username': self._username,
                'password': self._password,
                'otp_token': self._otp_token,
            }
            return data
        else:
            data = {
                'username': self._username,
                'password': self._password,
            }
            return data
        
