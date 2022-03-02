"""Module responsible for preparing an API request."""
import abc
import logging
from typing import Dict, Optional


logger = logging.getLogger(__name__)


class APIRequest(abc.ABC):
    """API request base class. ALL requests should inherit from this class."""

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

    @property
    def files(self) -> Optional[Dict]:
        """Files of the API request, containing the binary data."""
        return None
