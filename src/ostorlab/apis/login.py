from typing import Dict, Optional

from . import request
"""Abstract Base Class with the different endpoints used for API calls 
"""

class UsernamePasswordLoginAPIRequest(request.APIRequest):  
    """Makes a request to log in the user
    """    

    def __init__(self, username: str, password: str, otp_token: Optional[str] = None) -> None:
        """Constructs all the necessary attributes for the object.

        Args:
            username: the username (email) used to login.
            password: the password used to login.
            otp_token: the OTP or static code if required by the organisation the user belongs to. Defaults to None.
        """        
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
        """Gets the user login credentials.

        Returns:
            The user login credentials.
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
        
