"""Unittests for the agent details API request."""

import json

from ostorlab.apis import agent_details


def testAgentDetailsAPIRequest_whenUseExperimentalFalse_omitsUseExperimentalFromVariables() -> (
    None
):
    """Test that variables only contain agentKey when use_experimental is False (backward-compatible)."""
    api_request = agent_details.AgentDetailsAPIRequest(agent_key="agent/ostorlab/nmap")

    data = api_request.data
    variables = json.loads(data["variables"])

    assert variables == {"agentKey": "agent/ostorlab/nmap"}


def testAgentDetailsAPIRequest_whenUseExperimentalFalse_sendsQueryWithoutUseExperimentalArg() -> (
    None
):
    """Test that the original query form (without useExperimental) is sent by default for backward compat."""
    api_request = agent_details.AgentDetailsAPIRequest(agent_key="agent/ostorlab/nmap")

    query = api_request.query

    assert "$useExperimental" not in query
    assert "useExperimental:" not in query


def testAgentDetailsAPIRequest_whenUseExperimentalTrue_includesUseExperimentalInVariables() -> (
    None
):
    """Test that variables carry useExperimental: true when opted in."""
    api_request = agent_details.AgentDetailsAPIRequest(
        agent_key="agent/ostorlab/nmap", use_experimental=True
    )

    data = api_request.data
    variables = json.loads(data["variables"])

    assert variables == {"agentKey": "agent/ostorlab/nmap", "useExperimental": True}


def testAgentDetailsAPIRequest_whenUseExperimentalTrue_sendsQueryWithUseExperimentalArg() -> (
    None
):
    """Test that the experimental query form (with useExperimental) is sent when opted in."""
    api_request = agent_details.AgentDetailsAPIRequest(
        agent_key="agent/ostorlab/nmap", use_experimental=True
    )

    query = api_request.query

    assert "$useExperimental: Boolean" in query
    assert "useExperimental: $useExperimental" in query
