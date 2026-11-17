"""Request to fetch the GCP Cloud Logging service account credential for a scanner."""

from __future__ import annotations

import json
from typing import Any

from ostorlab.apis import request


class ScanLoggingCredentialAPIRequest(request.APIRequest):
    """Request the GCP Cloud Logging service account credential used by a scanner
    to ship its own logs and its agents' logs to GCP."""

    @property
    def query(self) -> str:
        """The query to fetch the scan logging credential.

        Returns:
            The query to fetch the scan logging credential.
        """
        return """
            query ScanLoggingCredential {
                scanLoggingCredential
            }
        """

    @property
    def data(self) -> dict[str, Any]:
        """Generates the request payload containing the query.

        Returns:
            The request payload with the query.
        """
        return {
            "query": self.query,
            "variables": json.dumps({}),
        }
