"""Paged active scans visible to a scanner's orchestration credentials."""

from __future__ import annotations

import json
import typing

from ostorlab.apis import request


class ScansActiveAPIRequest(request.APIRequest):
    """Read active scan IDs from the scanner endpoint."""

    def __init__(self, page: int) -> None:
        self._page = page

    @property
    def query(self) -> str:
        return """
        query ActiveScans($progresses: [String], $page: Int, $numberElements: Int) {
          scans(progresses: $progresses, page: $page, numberElements: $numberElements) {
            scans { id }
            pageInfo { numPages }
          }
        }
        """

    @property
    def data(self) -> dict[str, typing.Any]:
        return {
            "query": self.query,
            "variables": json.dumps(
                {
                    "progresses": ["in_progress"],
                    "page": self._page,
                    "numberElements": 100,
                }
            ),
        }
