"""Create mobile scan API."""

import enum
import io
import json
from typing import Dict, Optional, BinaryIO, List

from . import request

SCAN_PROFILES = {
    "fast_scan": "Fast Scan",
    "full_scan": "Full Scan",
    "full_web_scan": "Full Web Scan",
    # aliases
    "fast": "Fast Scan",
    "full": "Full Scan",
    "full_web": "Full Web Scan",
}


class MobileAssetType(enum.Enum):
    ANDROID = enum.auto()
    IOS = enum.auto()


class CreateMobileScanAPIRequest(request.APIRequest):
    """Create mobile scan API from a file."""

    def __init__(
        self,
        title: str,
        asset_type: MobileAssetType,
        scan_profile: str,
        application: BinaryIO,
        test_credential_ids: Optional[List[int]] = None,
        sboms: list[io.FileIO] = None,
    ):
        self._title = title
        self._asset_type = asset_type
        self._scan_profile = scan_profile
        self._application = application
        self._test_credential_ids = test_credential_ids
        self._sboms = sboms

    @property
    def query(self) -> Optional[str]:
        """Defines the query to create a mobile scan.

        Returns:
            The query to create a mobile scan
        """

        return """
mutation MobileScan($title: String!, $assetType: String!, $application: Upload!, $sboms: [Upload!], $scanProfile: String!, $credentialIds: [Int]) {
  createMobileScan(title: $title, assetType: $assetType, application: $application, sboms: $sboms, scanProfile: $scanProfile, credentialIds: $credentialIds) {
    scan {
      id
    }
  }
}
        """

    @property
    def data(self) -> Optional[Dict]:
        """Sets the query and variables to create the scan.

        Returns:
            The query and variables to create a scan.
        """

        var_map = {"0": ["variables.application"]}
        for idx, _ in enumerate(self._sboms):
            var_map[str(idx + 1)] = [f"variables.sboms.{idx}"]

        data = {
            "operations": json.dumps(
                {
                    "query": self.query,
                    "variables": {
                        "title": self._title,
                        "assetType": self._asset_type.name.lower(),
                        "application": None,
                        "scanProfile": self._scan_profile,
                        "credentialIds": self._test_credential_ids,
                        "sboms": [None for _ in self._sboms],
                    },
                }
            ),
            "map": json.dumps(var_map),
        }
        return data

    @property
    def files(self) -> Optional[Dict]:
        """Sets the file for multipart upload to create the mobile scan.

        Returns:
            The file mapping to create a scan.
        """
        files = {"0": self._application}
        for idx, sbom_file in enumerate(self._sboms):
            files[str(idx + 1)] = sbom_file
        return files


class CreateWebScanAPIRequest(request.APIRequest):
    """Create web scan API from a file."""

    def __init__(
        self,
        title: str,
        urls: [List[str]],
        scan_profile: str,
        sboms: Optional[list[io.FileIO]] = None,
        api_schema: Optional[io.FileIO] = None,
        proxy: Optional[str] = None,
        qps: Optional[int] = None,
        filtered_url_regexes: [List[str]] = None,
        test_credential_ids: List[int] = None,
    ):
        self._title = title
        self._urls = urls
        self._scan_profile = scan_profile
        self._api_schema = api_schema
        self._sboms = sboms
        self._proxy = proxy
        self._qps = qps
        self._filtered_url_regexes = filtered_url_regexes
        self._test_credential_ids = test_credential_ids

    @property
    def query(self) -> Optional[str]:
        """Defines the query to create a web scan.

        Returns:
            The query to create a web scan
        """

        return """
mutation WebScan($title: String!, $urls: [String]!, $scanProfile: String!, $sboms: [Upload!], $apiSchema: Upload, $proxy: String, $qps: Int, $filteredUrlRegexes: [String], $credentialIds: [Int]) {
  createWebScan(title: $title, urls: $urls, scanProfile: $scanProfile, sboms: $sboms, apiSchema: $apiSchema, proxy: $proxy, qps: $qps, filteredUrlRegexes: $filteredUrlRegexes, credentialIds: $credentialIds) {
    scan {
      id
    }
  }
}
        """

    @property
    def data(self) -> Optional[Dict]:
        """Sets the query and variables to create the scan.

        Returns:
            The query and variables to create a scan.
        """

        var_map = {}
        for idx, _ in enumerate(self._sboms):
            var_map[str(idx)] = [f"variables.sboms.{idx}"]

        if self._api_schema is not None:
            var_map[str(len(self._sboms))] = ["variables.apiSchema"]

        if len(var_map) > 0:
            data = {
                "operations": json.dumps(
                    {
                        "query": self.query,
                        "variables": {
                            "title": self._title,
                            "urls": self._urls,
                            "scanProfile": self._scan_profile,
                            "apiSchema": None,
                            "credentialIds": self._test_credential_ids,
                            "filteredUrlRegexes": self._filtered_url_regexes,
                            "proxy": self._proxy,
                            "qps": self._qps,
                            "sboms": [None for _ in self._sboms],
                        },
                    }
                ),
                "map": json.dumps(var_map),
            }
        else:
            data = {
                "query": self.query,
                "variables": json.dumps(
                    {
                        "title": self._title,
                        "urls": self._urls,
                        "scanProfile": self._scan_profile,
                        "apiSchema": None,
                        "credentialIds": self._test_credential_ids,
                        "filteredUrlRegexes": self._filtered_url_regexes,
                        "proxy": self._proxy,
                        "qps": self._qps,
                        "sboms": [None for _ in self._sboms],
                    }
                ),
            }
        return data

    @property
    def files(self) -> Optional[Dict]:
        """Sets the file for multipart upload to create the web scan.

        Returns:
            The file mapping to create a scan.
        """
        files = {}
        for idx, sbom_file in enumerate(self._sboms):
            files[str(idx)] = sbom_file

        if self._api_schema is not None:
            files[str(len(self._sboms))] = self._api_schema

        return files
