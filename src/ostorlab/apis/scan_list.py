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
         query Scans {
            scans {
                pageInfo {
                    hasNext
                    hasPrevious
                    count
                    numPages
                }
                scans {
                    title
                    assetType
                    riskRating
                    version
                    packageName
                    b64Icon
                    id
                    progress
                    messageStatus
                    createdTime
                    plan
                    hasAnalysis
                    asset {
                    __typename
                    ... on AndroidStoreAssetType {
                        applicationName
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
        data = {'query': self.query}
        return data
