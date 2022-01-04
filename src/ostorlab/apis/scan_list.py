"""Lists the remote scans."""

from ostorlab.apis import request
from typing import Dict, Optional
import json
import logging

logger = logging.getLogger(__name__)


class ScansListAPIRequest(request.APIRequest):
    """Lists the remote scans."""

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
                    asset {
                    ... on AndroidStoreAssetType {
                        packageName
                    }
                    ... on IOSStoreAssetType {
                        applicationName
                        packageName
                    }
                    ... on UrlAssetType {
                        urls
                    }
                    ... on DomainAssetType {
                        domain
                    }
                    }
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
        data = {
            'query': self.query,
            'variables': json.dumps({'page': 1, 'numberElements': 5})
            }
        return data
