"""Lists full details of vulnz."""

import json
from typing import Dict, Optional

from ostorlab.apis import request


class ScanVulnzDescribeAPIRequest(request.APIRequest):
    """Lists the remote vulnz of a scan."""

    def __init__(self, scan_id: int, vuln_id: int = None, page: int = 1):
        self._scan_id = scan_id
        self._vuln_id = vuln_id
        self._page = page

    @property
    def query(self) -> Optional[str]:
        """Defines the query to list the vulnz.

        Returns:
            The query to list the vulnz.
        """
        return """
            query Vulnerabilities(
                $scanId: Int!
                $vulnerabilityId: Int
                $page: Int!
                $numberElements: Int!
              ) {
                scan(scanId: $scanId) {
                  isEditable
                  vulnerabilities(
                    vulnerabilityId: $vulnerabilityId
                    page: $page
                    numberElements: $numberElements
                  ) {
                    pageInfo {
                      hasNext
                      hasPrevious
                      count
                      numPages
                    }
                    vulnerabilities {
                      id
                      technicalDetail
                      technicalDetailFormat
                      customRiskRating
                      customCvssV3BaseScore
                      falsePositive
                      detail {
                        title
                        shortDescription
                        description
                        recommendation
                        cvssV3Vector
                        references {
                          title
                          url
                        }
                      }
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
        data = dict(query=self.query, variables=json.dumps(
            {'scanId': self._scan_id, 'vulnerabilityId': self._vuln_id, 'page': self._page, 'numberElements': 10}))
        return data
