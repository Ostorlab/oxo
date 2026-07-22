"""Module responsible for preparing an API request."""

import abc
import logging
from typing import Dict, Optional, Any


logger = logging.getLogger(__name__)

SCANNER_GRAPHQL_ENDPOINT = "https://scanner.ostorlab.co/orchestrator/graphql"


class APIRequest(abc.ABC):
    """API request base class. ALL requests should inherit from this class."""

    @property
    def endpoint(self) -> Optional[str]:
        """API Endpoint. If None, the runner's default endpoint is used."""
        return None

    @property
    @abc.abstractmethod
    def query(self) -> Optional[str]:
        """Query to the GraphQL API."""
        raise NotImplementedError("Missing implementation")

    @property
    @abc.abstractmethod
    def data(self) -> Optional[Dict[str, Any]]:
        """Body of the API request, containing the query & any additional data."""
        raise NotImplementedError("Missing implementation")

    @property
    def files(self) -> Optional[Dict[str, Any]]:
        """Files of the API request, containing the binary data."""
        return None

    @property
    def is_json(self) -> bool:
        """Indicates if the request should be sent as JSON (default False)."""
        return False
