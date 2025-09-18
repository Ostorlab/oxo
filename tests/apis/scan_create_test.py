"""Unittests for the scan create API request with UI automation rules."""

import io
import json
from unittest import mock

from ostorlab.apis import scan_create


def testCreateUIPromptsAPIRequest_whenUIPromptsProvided_createsCorrectQuery() -> None:
    """Test CreateUIPromptsAPIRequest creates correct GraphQL query."""
    ui_prompts = [
        {"code": "Ensure full coverage of the app"},
        {"code": "Ensure login works"},
    ]

    api_request = scan_create.CreateUIPromptsAPIRequest(ui_prompts=ui_prompts)

    query = api_request.query
    assert "mutation CreateUIPrompts" in query
    assert "$uiPrompts: [UIAutomationRulesInputType]!" in query
    assert "createUiPrompts(uiPrompts: $uiPrompts)" in query
    assert "id" in query and "code" in query


def testCreateUIPromptsAPIRequest_whenUIPromptsProvided_includesUIPromptsInVariables() -> (
    None
):
    """Test CreateUIPromptsAPIRequest includes UI prompts in GraphQL variables."""
    ui_prompts = [
        {"code": "Ensure full coverage of the app"},
        {"code": "Ensure login works"},
    ]

    api_request = scan_create.CreateUIPromptsAPIRequest(ui_prompts=ui_prompts)

    data = api_request.data
    assert "query" in data
    assert "variables" in data
    assert data["variables"]["uiPrompts"] == ui_prompts


def testCreateUIPromptsAPIRequest_whenCalled_returnsNoFiles() -> None:
    """Test CreateUIPromptsAPIRequest returns no files."""
    ui_prompts = [{"code": "Ensure full coverage of the app"}]

    api_request = scan_create.CreateUIPromptsAPIRequest(ui_prompts=ui_prompts)

    files = api_request.files
    assert files is None


def testCreateMobileScanAPIRequest_whenUIAutomationRuleIdsProvided_includesUIAutomationRuleInstancesInVariables() -> (
    None
):
    """Test CreateMobileScanAPIRequest includes UI automation rule instances in GraphQL variables."""
    ui_automation_rule_ids = [1, 2]

    file_mock = mock.Mock(spec=io.FileIO)
    api_request = scan_create.CreateMobileScanAPIRequest(
        title="Test Scan",
        asset_type=scan_create.MobileAssetType.ANDROID,
        scan_profile="Full Scan",
        application=file_mock,
        sboms=[],
        ui_automation_rule_ids=ui_automation_rule_ids,
    )

    data = api_request.data
    operations = json.loads(data["operations"])
    variables = operations["variables"]
    assert "uiAutomationRuleInstances" in variables
    expected_ui_automation_rules = [
        {"ruleId": 1, "args": [{"name": "Rule 1"}]},
        {"ruleId": 2, "args": [{"name": "Rule 2"}]},
    ]
    assert variables["uiAutomationRuleInstances"] == expected_ui_automation_rules


def testCreateMobileScanAPIRequest_whenUIAutomationRuleIdsNotProvided_setsEmptyListInVariables() -> (
    None
):
    """Test CreateMobileScanAPIRequest sets empty list for UI automation rules when not provided."""
    file_mock = mock.Mock(spec=io.FileIO)
    api_request = scan_create.CreateMobileScanAPIRequest(
        title="Test Scan",
        asset_type=scan_create.MobileAssetType.ANDROID,
        scan_profile="Full Scan",
        application=file_mock,
        sboms=[],
    )

    data = api_request.data
    operations = json.loads(data["operations"])
    variables = operations["variables"]
    assert "uiAutomationRuleInstances" in variables
    assert variables["uiAutomationRuleInstances"] == []


def testCreateWebScanAPIRequest_whenUIAutomationRuleIdsProvided_includesUIAutomationRuleInstancesInVariables() -> (
    None
):
    """Test CreateWebScanAPIRequest includes UI automation rule instances in GraphQL variables."""
    ui_automation_rule_ids = [3, 4]

    api_request = scan_create.CreateWebScanAPIRequest(
        title="Test Web Scan",
        urls=["https://example.com"],
        scan_profile="Full Scan",
        sboms=[],
        ui_automation_rule_ids=ui_automation_rule_ids,
    )

    data = api_request.data
    variables = json.loads(data["variables"])
    assert "uiAutomationRuleInstances" in variables
    expected_ui_automation_rules = [
        {"ruleId": 3, "args": [{"name": "Rule 3"}]},
        {"ruleId": 4, "args": [{"name": "Rule 4"}]},
    ]
    assert variables["uiAutomationRuleInstances"] == expected_ui_automation_rules


def testCreateWebScanAPIRequest_whenUIAutomationRuleIdsNotProvided_setsEmptyListInVariables() -> (
    None
):
    """Test CreateWebScanAPIRequest sets empty list for UI automation rules when not provided."""
    api_request = scan_create.CreateWebScanAPIRequest(
        title="Test Web Scan",
        urls=["https://example.com"],
        scan_profile="Full Scan",
        sboms=[],
    )

    data = api_request.data
    variables = json.loads(data["variables"])
    assert "uiAutomationRuleInstances" in variables
    assert variables["uiAutomationRuleInstances"] == []


def testCreateMobileScanAPIRequest_UIAutomationRuleInstancesInQuery() -> None:
    """Test CreateMobileScanAPIRequest includes UI automation rule instances in GraphQL query."""
    file_mock = mock.Mock(spec=io.FileIO)
    api_request = scan_create.CreateMobileScanAPIRequest(
        title="Test Scan",
        asset_type=scan_create.MobileAssetType.ANDROID,
        scan_profile="Full Scan",
        application=file_mock,
        sboms=[],
        ui_automation_rule_ids=[],
    )

    query = api_request.query
    assert "uiAutomationRuleInstances: [UIAutomationRuleInstanceInputType]" in query
    assert "uiAutomationRuleInstances: $uiAutomationRuleInstances" in query


def testCreateWebScanAPIRequest_UIAutomationRuleInstancesInQuery() -> None:
    """Test CreateWebScanAPIRequest includes UI automation rule instances in GraphQL query."""
    api_request = scan_create.CreateWebScanAPIRequest(
        title="Test Web Scan",
        urls=["https://example.com"],
        scan_profile="Full Scan",
        sboms=[],
        ui_automation_rule_ids=[],
    )

    query = api_request.query
    assert "uiAutomationRuleInstances: [UIAutomationRuleInstanceInputType]" in query
    assert "uiAutomationRuleInstances: $uiAutomationRuleInstances" in query


def testCreateMobileScanAPIRequest_withMultipleUIAutomationRuleIds_createsCorrectStructure() -> (
    None
):
    """Test CreateMobileScanAPIRequest with multiple UI automation rule IDs creates correct structure."""
    ui_automation_rule_ids = [10, 20, 30]

    file_mock = mock.Mock(spec=io.FileIO)
    api_request = scan_create.CreateMobileScanAPIRequest(
        title="Test Scan",
        asset_type=scan_create.MobileAssetType.IOS,
        scan_profile="Full Scan",
        application=file_mock,
        sboms=[],
        ui_automation_rule_ids=ui_automation_rule_ids,
    )

    data = api_request.data
    operations = json.loads(data["operations"])
    variables = operations["variables"]

    expected_ui_automation_rules = [
        {"ruleId": 10, "args": [{"name": "Rule 10"}]},
        {"ruleId": 20, "args": [{"name": "Rule 20"}]},
        {"ruleId": 30, "args": [{"name": "Rule 30"}]},
    ]
    assert variables["uiAutomationRuleInstances"] == expected_ui_automation_rules
    assert variables["assetType"] == "ios"
    assert variables["title"] == "Test Scan"


def testCreateWebScanAPIRequest_withFilesAndUIAutomationRuleIds_usesOperationsFormat() -> (
    None
):
    """Test CreateWebScanAPIRequest with files and UI automation rule IDs uses operations format."""
    ui_automation_rule_ids = [5]
    sbom_mock = mock.Mock(spec=io.FileIO)

    api_request = scan_create.CreateWebScanAPIRequest(
        title="Test Web Scan",
        urls=["https://example.com", "https://test.com"],
        scan_profile="Full Web Scan",
        sboms=[sbom_mock],
        ui_automation_rule_ids=ui_automation_rule_ids,
    )

    data = api_request.data
    assert "operations" in data
    assert "map" in data

    operations = json.loads(data["operations"])
    variables = operations["variables"]
    assert variables["uiAutomationRuleInstances"] == [
        {"ruleId": 5, "args": [{"name": "Rule 5"}]}
    ]
    assert variables["urls"] == ["https://example.com", "https://test.com"]


def testCreateWebScanAPIRequest_withNoFilesButUIAutomationRuleIds_usesSimpleFormat() -> (
    None
):
    """Test CreateWebScanAPIRequest with no files but UI automation rule IDs uses simple format."""
    ui_automation_rule_ids = [7]

    api_request = scan_create.CreateWebScanAPIRequest(
        title="Test Web Scan",
        urls=["https://example.com"],
        scan_profile="Full Web Scan",
        sboms=[],
        ui_automation_rule_ids=ui_automation_rule_ids,
    )

    data = api_request.data
    assert "operations" not in data
    assert "map" not in data
    assert "query" in data
    assert "variables" in data

    variables = json.loads(data["variables"])
    assert variables["uiAutomationRuleInstances"] == [
        {"ruleId": 7, "args": [{"name": "Rule 7"}]}
    ]
