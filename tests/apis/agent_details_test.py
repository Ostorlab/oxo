"""Unittests for the agent details API request."""

import json

from ostorlab.apis import agent_details


def testAgentDetailsAPIRequest_whenNoReportingScanId_omitsReportingScanIdFromVariables() -> (
    None
):
    """Test that variables only contain agentKey when reporting_scan_id is not provided."""
    api_request = agent_details.AgentDetailsAPIRequest(agent_key="agent/ostorlab/nmap")

    data = api_request.data
    variables = json.loads(data["variables"])

    assert variables == {"agentKey": "agent/ostorlab/nmap"}


def testAgentDetailsAPIRequest_whenReportingScanIdProvided_includesReportingScanIdInVariables() -> (
    None
):
    """Test that variables contain reportingScanId when reporting_scan_id is provided."""
    api_request = agent_details.AgentDetailsAPIRequest(
        agent_key="agent/ostorlab/nmap", reporting_scan_id=42
    )

    data = api_request.data
    variables = json.loads(data["variables"])

    assert variables == {"agentKey": "agent/ostorlab/nmap", "reportingScanId": 42}


def testAgentDetailsAPIRequest_whenCalled_queryDeclaresReportingScanIdVariable() -> (
    None
):
    """Test that the GraphQL query declares and forwards the reportingScanId variable."""
    api_request = agent_details.AgentDetailsAPIRequest(agent_key="agent/ostorlab/nmap")

    query = api_request.query

    assert "$reportingScanId: Int" in query
    assert "reportingScanId: $reportingScanId" in query
