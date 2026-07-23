"""Create test credentials API."""

import abc
import dataclasses
import json
from typing import Any

from . import request


class TestCredential(abc.ABC):
    """Base abstract test credentials."""

    @abc.abstractmethod
    def to_variables(self) -> dict[str, Any]:
        """Generate query variables."""


@dataclasses.dataclass
class TestCredentialLogin(TestCredential):
    """Login password test credentials with optional role and url fields."""

    login: str
    password: str
    role: str | None = None
    url: str | None = None

    def to_variables(self) -> dict[str, Any]:
        """Generate query variables."""
        return {
            "testCredentials": {
                "loginPassword": {
                    "login": self.login,
                    "password": self.password,
                    "role": self.role,
                    "url": self.url,
                }
            }
        }

    def __repr__(self) -> str:
        return f"login: {self.login}, password: ************, role: {self.role}, url: {self.url}"


@dataclasses.dataclass
class TestCredentialCustom(TestCredential):
    """Custom test credentials with variable number of a pair of name and value."""

    values: dict[str, str]

    def to_variables(self) -> dict[str, Any]:
        """Generate query variables."""
        return {
            "testCredentials": {
                "custom": {
                    "credentials": [
                        {"name": n, "value": v} for (n, v) in self.values.items()
                    ]
                }
            }
        }


@dataclasses.dataclass
class TestCredentialEmail2FA(TestCredential):
    """Email 2FA test credentials."""

    sender_email_address: str
    email_address: str
    password: str

    def to_variables(self) -> dict[str, Any]:
        """Generate query variables."""
        return {
            "testCredentials": {
                "email2fa": {
                    "emailSender": self.sender_email_address,
                    "email": self.email_address,
                    "password": self.password,
                }
            }
        }


@dataclasses.dataclass
class TestCredentialSMS2FA(TestCredential):
    """SMS 2FA test credentials."""

    sender_phone_number: str

    def to_variables(self) -> dict[str, Any]:
        """Generate query variables."""
        return {
            "testCredentials": {
                "sms2fa": {
                    "phoneSender": self.sender_phone_number,
                }
            }
        }


@dataclasses.dataclass
class TestCredentialTOTP2FA(TestCredential):
    """TOTP 2FA test credentials."""

    totp_seed: str

    def to_variables(self) -> dict[str, Any]:
        """Generate query variables."""
        return {
            "testCredentials": {
                "totp2fa": {
                    "totpSecret": self.totp_seed,
                }
            }
        }


class CreateTestCredentialAPIRequest(request.APIRequest):
    """Create mobile scan API from a file."""

    def __init__(self, test_credential: TestCredential):
        self._test_credential = test_credential

    @property
    def query(self) -> str | None:
        """Defines the query to create test credentials.

        Returns:
            The query to create a test credential.
        """

        return """
mutation TestCredentials($testCredentials: TestCredentialsInput!) {
  createTestCredentials(testCredentials: $testCredentials) {
    testCredentials {
      ... on CustomTestCredentials {
        id
      }
      ... on LoginPasswordTestCredentials {
        id
      }
      ... on Email2FATestCredentials {
        id
      }
      ... on Sms2FATestCredentials {
        id
      }
      ... on Totp2FATestCredentials {
        id
      }
    }
  }
}
        """

    @property
    def data(self) -> dict[str, Any] | None:
        """Sets the query and variables to create test credentials.

        Returns:
            The query and variables to create test credentials.
        """
        data = {
            "query": self.query,
            "variables": json.dumps(self._test_credential.to_variables()),
        }
        return data
