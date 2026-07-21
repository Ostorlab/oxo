"""Discovery query to fetch pending/abandoned scans."""

from typing import Dict, Optional, Any

from ostorlab.apis import request

import json


class ScansDiscoverAPIRequest(request.APIRequest):
    """Discovery query API request."""

    @property
    def endpoint(self) -> str:
        """API endpoint."""
        return "https://scanner.ostorlab.co/orchestrator/graphql"

    @property
    def query(self) -> Optional[str]:
        return """
        query GetPendingScans($progresses: [String]) {
          scans(progresses: $progresses) {
            scans {
              id
            }
          }
        }
        """

    @property
    def data(self) -> Optional[Dict[str, Any]]:
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
