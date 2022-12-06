"""Makes a login request.

This code gets the username and password of a user and makes a login request to the token endpoint.
If an OTP token is required, the user must provide either an OTP code from their authenticator app or
a backed up static code in order to complete the authentication process.

    Typical usage example:

    login_request = login.UsernamePasswordLoginAPIRequest(username, password, otp_token)
"""

from typing import Dict, Optional

from ostorlab.apis import request


class UsernamePasswordLoginAPIRequest(request.APIRequest):
    """Makes a request to log in the user."""

    def __init__(
        self, username: str, password: str, otp_token: Optional[str] = None
    ) -> None:
        """Constructs all the necessary attributes for the object.

        Args:
            username: the username (email) used to login.
            password: the password used to login.
            otp_token: the OTP or static code if the user has enabled OTP. Defaults to None.
        """
        self._username = username
        self._password = password
        self._otp_token = otp_token

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
                "username": self._username,
                "password": self._password,
                "otp_token": self._otp_token,
            }
            return data
        else:
            data = {
                "username": self._username,
                "password": self._password,
            }
            return data
