"""Lists the remote scans."""

import json
from typing import Any

from ostorlab.apis import request


class ScansListAPIRequest(request.APIRequest):
    """Lists the remote scans."""

    def __init__(self, page: int, elements: int, state: str | None = None):
        self._page = page
        self._elements = elements
        self._state = state

    @property
    def query(self) -> str | None:
        """Defines the query to list the scans.

        Returns:
            The query to list the scans.
        """
        return """
         query Scans($page: Int, $numberElements: Int, $state: String) {
            scans(page: $page, numberElements: $numberElements, state: $state) {
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
                    scanProfile
                }
            }
         }
        """

    @property
    def data(self) -> dict[str, Any] | None:
        """Sets the query to list the scans.

        Returns:
              The query to list the scans.
        """
        variables: dict[str, Any] = {
            "page": self._page,
            "numberElements": self._elements,
        }
        if self._state is not None:
            variables["state"] = self._state
        data = {
            "query": self.query,
            "variables": json.dumps(variables),
        }
        return data
