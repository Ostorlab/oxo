"""Lists the remote vulnz."""

import json
from typing import Dict, Optional

from ostorlab.apis import request


class VulnzListAPIRequest(request.APIRequest):
    """Lists the remote vulnz of a scan."""

    def __init__(self, scan_id: int):
        self._scan_id = scan_id

    @property
    def query(self) -> Optional[str]:
        """Defines the query to list the vulnz.

        Returns:
            The query to list the vulnz.
        """
        return """
        query Scan($scanId: Int!) {
            scan(scanId: $scanId) {
              kbVulnerabilities {
                highestRiskRating
                highestCvssV3BaseScore
                kb {
                  id
                  title
                  shortDescription
                  cvssV3Vector
                }
              }
            }
        }
        """

    @property
    def data(self) -> Optional[Dict]:
        """Sets the query to list the vulnz.

        Returns:
              The query to list the vulnz.
        """
        data = {
            'query': self.query,
            'variables': json.dumps({'scanId': self._scan_id})
        }
        return data
