"""Update scan state request."""

import json
from typing import Any, Literal

from ostorlab.apis import request


class ScanUpdateStateAPIRequest(request.APIRequest):
    """State update mutation API request (Start / Rollback / Finish)."""

    def __init__(
        self, scan_id: int, progress: Literal["started", "rolled_back", "finished"]
    ) -> None:
        self._scan_id = scan_id
        self._progress = progress

    @property
    def endpoint(self) -> str:
        """API endpoint."""
        return request.SCANNER_GRAPHQL_ENDPOINT

    @property
    def query(self) -> str | None:
        return """
        mutation UpdateScanState($scanId: Int!, $progress: String!) {
          updateScan(scanId: $scanId, progress: $progress, deviceId: null) {
            success
            message
            scan {
              id
              progress
            }
          }
        }
        """

    @property
    def data(self) -> dict[str, Any] | None:
        return {
            "query": self.query,
            "variables": json.dumps(
                {"scanId": self._scan_id, "progress": self._progress}
            ),
        }
