"""TODO(mohsine):Wrtite docstring."""
import abc
import logging
from typing import Dict, Optional

AUTHENTICATED_GRAPHQL_ENDPOINT = 'https://api.ostorlab.co/apis/graphql'
PUBLIC_GRAPHQL_ENDPOINT = 'https://api.ostorlab.co/apis/public'
TOKEN_ENDPOINT = 'https://api.ostorlab.co/apis/token/'

logger = logging.getLogger(__name__)


class APIRequest(abc.ABC):
    """TODO(mohsine):Wrtite docstring."""

    @property
    def endpoint(self):
        return AUTHENTICATED_GRAPHQL_ENDPOINT

    @property
    @abc.abstractmethod
    def query(self) -> Optional[str]:
        raise NotImplementedError('Missing implementation')

    @property
    @abc.abstractmethod
    def data(self) -> Optional[Dict]:
        raise NotImplementedError('Missing implementation')
