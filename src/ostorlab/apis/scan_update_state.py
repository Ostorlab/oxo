"""Update scan state request."""

import json
from typing import Any

from ostorlab.apis import request


class ScanUpdateStateAPIRequest(request.APIRequest):
    """State update mutation API request."""

    def __init__(self, scan_id: int, progress: str, full_details: bool = False) -> None:
        self._scan_id = scan_id
        self._progress = progress
        self._full_details = full_details

    @property
    def query(self) -> str | None:
        if self._full_details is True:
            return """
            mutation UpdateScanState($scanId: Int!, $progress: String!) {
              updateScan(scanId: $scanId, progress: $progress) {
                success
                message
                scan {
                  id
                  progress
                  asset {
                    __typename
                    ... on UrlAssetType { urls apiSchema }
                    ... on Ipv4AssetType { host version mask }
                    ... on Ipv6AssetType { host version mask }
                    ... on IpAssetType { host version mask }
                    ... on AndroidApkAssetType { path contentUrl }
                    ... on DomainNameAssetType { name }
                    ... on AndroidPackageNameAssetType { packageName }
                    ... on IosBundleIdAssetType { bundleId }
                    ... on IosTestflightAssetType { applicationUrl }
                    ... on AndroidAabAssetType { path contentUrl }
                    ... on IosIpaAssetType { path contentUrl }
                    ... on SourceCodeAssetType { path contentUrl language }
                    ... on FileAssetType { path contentUrl }
                    ... on TicketAssetType { ticketId ticketKey title description }
                    ... on HarmonyOsBundleNameAssetType { bundleName }
                    ... on HarmonyOsApkAssetType { path contentUrl }
                    ... on HarmonyOsAabAssetType { path contentUrl }
                    ... on HarmonyOsHapAssetType { path contentUrl }
                    ... on HarmonyOsAppAssetType { path contentUrl }
                    ... on HarmonyOsRpkAssetType { path contentUrl }
                    ... on NetworkAssetType { networks }
                    ... on AgentAssetType { key version gitLocation dockerLocation yamlFileLocation }
                    ... on RiskAssetType { description rating target risksGroup }
                    ... on RisksAssetType { id }
                    ... on RepositoryAssetType { provider repositoryUrl commitHash }
                    ... on RepositoryArchiveAssetType { path contentUrl }
                  }
                  agentGroup {
                    key
                    agents {
                      key
                      version
                      replicas
                      caps
                      cyclicProcessingLimit
                      depthProcessingLimit
                      inSelectors
                      serviceName
                      openPorts {
                        srcPort
                        destPort
                      }
                      args {
                        name
                        type
                        value
                      }
                    }
                  }
                }
              }
            }
            """
        else:
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
