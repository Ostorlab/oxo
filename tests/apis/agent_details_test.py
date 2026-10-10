"""Unittests for the agent details API request."""

import json

from ostorlab.apis import agent_details


def testAgentDetailsAPIRequest_whenUseExperimentalFalse_sendsUseExperimentalFalseInVariables() -> (
    None
):
    """Test that variables include useExperimental: False when use_experimental is not set."""
    api_request = agent_details.AgentDetailsAPIRequest(agent_key="agent/ostorlab/nmap")

    data = api_request.data
    variables = json.loads(data["variables"])

    assert variables == {"agentKey": "agent/ostorlab/nmap", "useExperimental": False}


def testAgentDetailsAPIRequest_whenUseExperimentalFalse_sendsQueryWithUseExperimentalArg() -> (
    None
):
    """Test that the query always includes the useExperimental argument regardless of value."""
    api_request = agent_details.AgentDetailsAPIRequest(agent_key="agent/ostorlab/nmap")

    query = api_request.query

    assert "$useExperimental: Boolean" in query
    assert "useExperimental: $useExperimental" in query


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


def testAgentDetailsAPIRequest_whenNoChannel_queryAndVariablesDoNotMentionChannel() -> (
    None
):
    """Test that a request without a channel stays compatible with stores without the channel argument."""
    api_request = agent_details.AgentDetailsAPIRequest(
        agent_key="agent/ostorlab/nmap", use_experimental=True
    )

    data = api_request.data
    variables = json.loads(data["variables"])

    assert "channel" not in data["query"]
    assert variables == {"agentKey": "agent/ostorlab/nmap", "useExperimental": True}


def testAgentDetailsAPIRequest_whenChannelIsSet_sendsChannelVariableAndArgument() -> (
    None
):
    """Test that a channel is declared, passed to versions and sent with useExperimental."""
    api_request = agent_details.AgentDetailsAPIRequest(
        agent_key="agent/ostorlab/nmap", channel="beta"
    )

    data = api_request.data
    variables = json.loads(data["variables"])

    assert "$channel: String" in data["query"]
    assert "channel: $channel" in data["query"]
    assert "useExperimental: $useExperimental" in data["query"]
    assert variables == {
        "agentKey": "agent/ostorlab/nmap",
        "useExperimental": False,
        "channel": "beta",
    }
