"""Create mobile scan API."""

import enum
import io
import json
import dataclasses
from typing import Dict, Optional, BinaryIO, List, Any

from . import request


class CreateUIPromptsAPIRequest(request.APIRequest):
    """Create UI prompts API request with get_or_create logic."""

    def __init__(self, ui_prompts: List[Dict[str, Any]]):
        self._ui_prompts = ui_prompts

    @property
    def query(self) -> str:
        """Defines the query to create UI prompts.

        Returns:
            The query to create UI prompts
        """
        return """
mutation CreateUIPrompts($uiPrompts: [UIAutomationRulesInputType]!) {
  createUiPrompts(uiPrompts: $uiPrompts) {
    uiPrompts {
      id
      name
      code
    }
  }
}
        """

    @property
    def data(self) -> Dict[str, Any]:
        """Sets the query and variables to create UI prompts.

        Returns:
            The query and variables to create UI prompts.
        """
        return {
            "query": self.query,
            "variables": json.dumps({"uiPrompts": self._ui_prompts}),
        }

    @property
    def is_json(self) -> bool:
        """Indicates that the request should be sent as JSON.

        Returns:
            True if the request should be sent as JSON.
        """
        return True


@dataclasses.dataclass
class ScanSource:
    """Dataclass holding scan source related parameters."""

    source: str
    repository: Optional[str] = None
    pr_number: Optional[str] = None
    branch: Optional[str] = None


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
        scope_urls_regexes: Optional[List[str]] = None,
        sboms: list[io.FileIO] = None,
        scan_source: Optional[ScanSource] = None,
        ui_automation_rule_ids: List[int] = (),
    ):
        self._title = title
        self._asset_type = asset_type
        self._scan_profile = scan_profile
        self._application = application
        self._test_credential_ids = test_credential_ids
        self._scope_urls_regexes = scope_urls_regexes
        self._sboms = sboms
        self._scan_source = scan_source
        self._ui_automation_rule_ids = ui_automation_rule_ids

    @property
    def query(self) -> Optional[str]:
        """Defines the query to create a mobile scan.

        Returns:
            The query to create a mobile scan
        """

        return """
mutation MobileScan($title: String!, $assetType: String!, $application: Upload!, $sboms: [Upload!], $scanProfile: String!, $credentialIds: [Int], $scanSource: ScanSourceInputType, $scopeUrlsRegexes: [String], $uiAutomationRuleInstances: [UIAutomationRuleInstanceInputType]) {
  createMobileScan(title: $title, assetType: $assetType, application: $application, sboms: $sboms, scanProfile: $scanProfile, credentialIds: $credentialIds, scanSource: $scanSource, scopeUrlsRegexes: $scopeUrlsRegexes, uiAutomationRuleInstances: $uiAutomationRuleInstances) {
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
                        "scanSource": {
                            "source": self._scan_source.source,
                            "repository": self._scan_source.repository,
                            "prNumber": self._scan_source.pr_number,
                            "branch": self._scan_source.branch,
                        }
                        if self._scan_source is not None
                        else None,
                        "scopeUrlsRegexes": self._scope_urls_regexes,
                        "uiAutomationRuleInstances": [
                            {
                                "ruleId": rule_id,
                                "args": [{"name": f"Rule {rule_id}"}],
                            }
                            for rule_id in self._ui_automation_rule_ids
                        ],
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
        urls: List[str],
        scan_profile: str,
        sboms: Optional[list[io.FileIO]] = None,
        api_schema: Optional[io.FileIO] = None,
        proxy: Optional[str] = None,
        qps: Optional[int] = None,
        filtered_url_regexes: Optional[List[str]] = None,
        test_credential_ids: Optional[List[int]] = None,
        ui_automation_rule_ids: List[int] = (),
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
        self._ui_automation_rule_ids = ui_automation_rule_ids

    @property
    def query(self) -> Optional[str]:
        """Defines the query to create a web scan.

        Returns:
            The query to create a web scan
        """

        return """
mutation WebScan($title: String!, $urls: [String]!, $scanProfile: String!, $sboms: [Upload!], $apiSchema: Upload, $proxy: String, $qps: Int, $filteredUrlRegexes: [String], $credentialIds: [Int], $uiAutomationRuleInstances: [UIAutomationRuleInstanceInputType]) {
  createWebScan(title: $title, urls: $urls, scanProfile: $scanProfile, sboms: $sboms, apiSchema: $apiSchema, proxy: $proxy, qps: $qps, filteredUrlRegexes: $filteredUrlRegexes, credentialIds: $credentialIds, uiAutomationRuleInstances: $uiAutomationRuleInstances) {
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
                            "uiAutomationRuleInstances": [
                                {
                                    "ruleId": rule_id,
                                    "args": [{"name": f"Rule {rule_id}"}],
                                }
                                for rule_id in self._ui_automation_rule_ids
                            ],
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
                        "uiAutomationRuleInstances": [
                            {
                                "ruleId": rule_id,
                                "args": [{"name": f"Rule {rule_id}"}],
                            }
                            for rule_id in self._ui_automation_rule_ids
                        ],
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
