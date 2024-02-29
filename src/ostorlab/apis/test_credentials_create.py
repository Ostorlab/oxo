"""Create test credentials API."""

import abc
import dataclasses
import json
from typing import Dict, Optional, Any

from . import request


class TestCredential(abc.ABC):
    """Base abstract test credentials."""

    @abc.abstractmethod
    def to_variables(self) -> Dict[str, Any]:
        """Generate query variables."""
        pass


@dataclasses.dataclass
class TestCredentialLogin(TestCredential):
    """Loging password test credentials with optional role and url fields."""

    login: str
    password: str
    role: Optional[str] = None
    url: Optional[str] = None

    def to_variables(self) -> Dict[str, Any]:
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


@dataclasses.dataclass
class TestCredentialCustom(TestCredential):
    """Custom test credentials with variable number of a pair of name and value."""

    values: Dict[str, str]

    def to_variables(self) -> Dict[str, Any]:
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


class CreateTestCredentialAPIRequest(request.APIRequest):
    """Create mobile scan API from a file."""

    def __init__(self, test_credential: TestCredential):
        self._test_credential = test_credential

    @property
    def query(self) -> Optional[str]:
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
    }
  }
}
        """

    @property
    def data(self) -> Optional[Dict]:
        """Sets the query and variables to create test credentials.

        Returns:
            The query and variables to create test credentials.
        """
        data = {
            "query": self.query,
            "variables": json.dumps(self._test_credential.to_variables()),
        }
        return data
