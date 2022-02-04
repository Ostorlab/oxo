""""""
import abc
import logging
from typing import Dict, Optional

AUTHENTICATED_GRAPHQL_ENDPOINT = 'https://api.ostorlab.co/apis/graphql'
PUBLIC_GRAPHQL_ENDPOINT = 'https://api.ostorlab.co/apis/public_graphql'
TOKEN_ENDPOINT = 'https://api.ostorlab.co/apis/token/'

logger = logging.getLogger(__name__)


class APIRequest(abc.ABC):
    """API request base class. ALL requests should inherit from this class."""

    @property
    def endpoint(self):
        """Endpoint of the request."""
        return AUTHENTICATED_GRAPHQL_ENDPOINT

    @property
    @abc.abstractmethod
    def query(self) -> Optional[str]:
        """Query to the GraphQL API."""
        raise NotImplementedError('Missing implementation')

    @property
    @abc.abstractmethod
    def data(self) -> Optional[Dict]:
        """Body of the API request, containing the query & any additional data."""
        raise NotImplementedError('Missing implementation')
