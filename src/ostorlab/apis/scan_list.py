"""Lists the remote scans."""

from ostorlab.apis import request
from typing import Dict, Optional
import json
import logging

logger = logging.getLogger(__name__)

class ScansListAPIRequest(request.APIRequest):
    """Lists the remote scans."""

    def __init__(self, page: int, elements: int):
        self._page = page
        self._elements = elements

    @property
    def query(self) -> Optional[str]:
        """Defines the query to list the scans.

        Returns:
            The query to list the scans.
        """
        return """
         query Scans($page: Int, $numberElements: Int) {
            scans(page: $page, numberElements: $numberElements) {
                pageInfo {
                    hasNext
                    hasPrevious
                    count
                    numPages
                }
                scans {
                    assetType
                    riskRating
                    version
                    packageName
                    id
                    progress
                    createdTime
                    plan
                }
            }
         }
        """

    @property
    def endpoint(self):
        return request.AUTHENTICATED_GRAPHQL_ENDPOINT

    @property
    def data(self) -> Optional[Dict]:
        """Sets the query to list the scans.

        Returns:
              The query to list the scans.
        """
        logger.info(self._page)
        data = {
            'query': self.query,
            'variables': json.dumps({'page': self._page, 'numberElements': self._elements})
            }
        return data
