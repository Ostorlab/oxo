"""Unittests for the scan create API request with UI automation rules."""

import io
import json
from unittest import mock

from ostorlab.apis import scan_create


def testCreateMobileScanAPIRequest_whenUIAutomationRulesProvided_includesUIAutomationRulesInVariables():
    """Test CreateMobileScanAPIRequest includes UI automation rules in GraphQL variables."""
    ui_automation_rules = [
        {"rule_id": 1, "args": [{"name": "username", "value": "testuser"}]}
    ]

    file_mock = mock.Mock(spec=io.FileIO)
    api_request = scan_create.CreateMobileScanAPIRequest(
        title="Test Scan",
        asset_type=scan_create.MobileAssetType.ANDROID,
        scan_profile="Full Scan",
        application=file_mock,
        sboms=[],
        ui_automation_rule_instances=ui_automation_rules,
    )

    data = api_request.data
    operations = json.loads(data["operations"])
    variables = operations["variables"]
    assert "uiAutomationRuleInstances" in variables
    assert variables["uiAutomationRuleInstances"] == ui_automation_rules


def testCreateMobileScanAPIRequest_whenUIAutomationRulesNotProvided_setsNullInVariables():
    """Test CreateMobileScanAPIRequest sets null for UI automation rules when not provided."""
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
    assert variables["uiAutomationRuleInstances"] is None


def testCreateWebScanAPIRequest_whenUIAutomationRulesProvided_includesUIAutomationRulesInVariables():
    """Test CreateWebScanAPIRequest includes UI automation rules in GraphQL variables."""
    ui_automation_rules = [
        {"rule_id": 2, "args": [{"name": "password", "value": "testpass"}]}
    ]

    api_request = scan_create.CreateWebScanAPIRequest(
        title="Test Web Scan",
        urls=["https://example.com"],
        scan_profile="Full Scan",
        sboms=[],
        ui_automation_rule_instances=ui_automation_rules,
    )

    data = api_request.data
    variables = json.loads(data["variables"])
    assert "uiAutomationRuleInstances" in variables
    assert variables["uiAutomationRuleInstances"] == ui_automation_rules


def testCreateWebScanAPIRequest_whenUIAutomationRulesNotProvided_setsNullInVariables():
    """Test CreateWebScanAPIRequest sets null for UI automation rules when not provided."""
    api_request = scan_create.CreateWebScanAPIRequest(
        title="Test Web Scan",
        urls=["https://example.com"],
        scan_profile="Full Scan",
        sboms=[],
    )

    data = api_request.data
    variables = json.loads(data["variables"])
    assert "uiAutomationRuleInstances" in variables
    assert variables["uiAutomationRuleInstances"] is None


def testCreateMobileScanAPIRequest_UIAutomationRulesInQuery():
    """Test CreateMobileScanAPIRequest includes UI automation rules in GraphQL query."""
    file_mock = mock.Mock(spec=io.FileIO)
    api_request = scan_create.CreateMobileScanAPIRequest(
        title="Test Scan",
        asset_type=scan_create.MobileAssetType.ANDROID,
        scan_profile="Full Scan",
        application=file_mock,
        sboms=[],
        ui_automation_rule_instances=[],
    )

    query = api_request.query
    assert "uiAutomationRuleInstances: $uiAutomationRuleInstances" in query


def testCreateWebScanAPIRequest_UIAutomationRulesInQuery():
    """Test CreateWebScanAPIRequest includes UI automation rules in GraphQL query."""
    api_request = scan_create.CreateWebScanAPIRequest(
        title="Test Web Scan",
        urls=["https://example.com"],
        scan_profile="Full Scan",
        sboms=[],
        ui_automation_rule_instances=[],
    )

    query = api_request.query
    assert "uiAutomationRuleInstances: $uiAutomationRuleInstances" in query
