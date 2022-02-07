"""Stops a remote scan."""

from typing import Dict, Optional
import json

from ostorlab.apis import request


class ScanStopAPIRequest(request.APIRequest):
    """Stops a remote scan."""

    def __init__(self, scan_id: int):
        self._scan_id = scan_id

    @property
    def query(self) -> Optional[str]:
        """Defines the mutation to stop a scan.

        Returns:
            The mutation to stop a scan.
        """
        return """
         mutation StopScanMutation($scanId: Int!) {
            stopScan(scanId: $scanId) {
                scan {
                    id
                }
            }
         }
        """

    @property
    def data(self) -> Optional[Dict]:
        """Sets the mutation to stop a scan.

        Returns:
              The mutation to stop a scan.
        """
        data = {
            'query': self.query,
            'variables': json.dumps({'scanId': self._scan_id})
            }
        return data
