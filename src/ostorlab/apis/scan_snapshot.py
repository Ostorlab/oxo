"""Mark that a paused scan no longer resumes from a snapshot."""

import json
from typing import Any

from ostorlab.apis import request


class ClearScanSnapshotAPIRequest(request.APIRequest):
    """Clear the `hasSnapshot` flag of a scan, once it was restored or when its snapshot is lost.

    The scanning engine sets the flag when the stop scan agent confirms a pause; the scanner only clears it.
    """

    def __init__(self, scan_id: int) -> None:
        self._scan_id = scan_id

    @property
    def query(self) -> str | None:
        return """
        mutation ClearScanSnapshot($scanId: Int!) {
          updateScan(scanId: $scanId, hasSnapshot: false) {
            success
            message
          }
        }
        """

    @property
    def data(self) -> dict[str, Any] | None:
        return {
            "query": self.query,
            "variables": json.dumps({"scanId": self._scan_id}),
        }
