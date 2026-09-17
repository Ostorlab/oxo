"""Lists the remote vulnz."""

import json
from typing import Any

from ostorlab.apis import request


class VulnzListAPIRequest(request.APIRequest):
    """Lists the remote vulnz of a scan."""

    def __init__(
        self,
        scan_id: int,
        number_elements: int,
        page: int,
    ):
        self._scan_id = scan_id
        self._number_elements = number_elements
        self._page = page

    @property
    def query(self) -> str | None:
        """Defines the query to list the vulnz.

        Returns:
            The query to list the vulnz.
        """
        return """
        query Scan($scanId: Int!,$page:Int,$numberElements:Int) {
            scan(scanId: $scanId) {
                vulnerabilities (page:$page,numberElements:$numberElements){
                    pageInfo{
                        hasNext
                        numPages
                    }
                    vulnerabilities{
                        id
                        technicalDetail
                        vulnerabilityLocation {
                          asset {
                            ... on NGAndroidAppAssetType {
                              packageName
                            }
                            
                            ... on NGIOSAppAssetType {
                                bundleId
                            }
                            
                            ... on NGHarmonyOSAppAssetType {
                                bundleName
                            }
                            
                            ... on NGIPv6AssetType {
                                host
                            }
                            
                            ... on NGIPv4AssetType {
                                host
                            }
                            
                            ... on NGDomainAssetType {
                                name
                            }

                            ... on NGRepositoryAssetType {
                                repositoryUrl
                            }

                            ... on NGNodeType {
                                nodeType
                                nodeKey
                            }
                          }
                          metadata {
                            metadataType
                            metadataValue {
                              ... on VulnerabilityLocationMetadataStringType {
                                value
                              }
                            }
                          }
                        }
                        detail{
                          title
                          shortDescription
                          description
                          recommendation
                          cvssV3Vector
                          riskRating
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
    def data(self) -> dict[str, Any] | None:
        """Sets the query to list the vulnz.

        Returns:
              The query to list the vulnz.
        """
        data = {
            "query": self.query,
            "variables": json.dumps(
                {
                    "scanId": self._scan_id,
                    "page": self._page,
                    "numberElements": self._number_elements,
                }
            ),
        }
        return data
