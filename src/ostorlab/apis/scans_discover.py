"""Discovery query to fetch pending/abandoned scans."""

import json
from typing import Any

from ostorlab.apis import request


class ScansDiscoverAPIRequest(request.APIRequest):
    """Discovery query API request."""

    @property
    def endpoint(self) -> str:
        """API endpoint."""
        return "https://scanner.ostorlab.co/orchestrator/graphql"

    @property
    def query(self) -> str | None:
        return """
        query GetPendingScans($progresses: [String], $oldLockedScans: Boolean, $numberElements: Int) {
          scans(progresses: $progresses, oldLockedScans: $oldLockedScans, numberElements: $numberElements) {
            scans {
              id
            }
          }
        }
        """

    @property
    def data(self) -> dict[str, Any] | None:
        return {
            "query": self.query,
            "variables": json.dumps(
                {
                    "progresses": ["not_started", "locked"],
                    "oldLockedScans": True,
                    "numberElements": 50,
                }
            ),
        }
