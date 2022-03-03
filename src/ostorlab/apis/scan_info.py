"""Retrieve the scan info."""

from typing import Dict, Optional
import json

from ostorlab.apis import request


class ScanInfoAPIRequest(request.APIRequest):
    """Retrieve the scan info."""

    def __init__(self, scan_id: int):
        self._scan_id = scan_id

    @property
    def query(self) -> Optional[str]:
        """Defines the query to get the scan info.

        Returns:
            The query to get the scan info.
        """
        return """
         query scan($scanId: Int) {
            scan(scanId: $scanId) {
                progress
                riskRating
            }
         }
        """

    @property
    def data(self) -> Optional[Dict]:
        """Sets the query to scan info.

        Returns:
              The query to scan info.
        """
        data = {
            'query': self.query,
            'variables': json.dumps({'scanId': self._scan_id})
            }
        return data
