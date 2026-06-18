"""Unittests for the agent details API request."""

import json

from ostorlab.apis import agent_details


def testAgentDetailsAPIRequest_whenUseExperimentalNotProvided_defaultsFalseInVariables() -> (
    None
):
    """Test that useExperimental defaults to False in variables when not provided."""
    api_request = agent_details.AgentDetailsAPIRequest(agent_key="agent/ostorlab/nmap")

    data = api_request.data
    variables = json.loads(data["variables"])

    assert variables == {"agentKey": "agent/ostorlab/nmap", "useExperimental": False}


def testAgentDetailsAPIRequest_whenUseExperimentalTrue_setsTrueInVariables() -> None:
    """Test that variables carry useExperimental: true when opted in."""
    api_request = agent_details.AgentDetailsAPIRequest(
        agent_key="agent/ostorlab/nmap", use_experimental=True
    )

    data = api_request.data
    variables = json.loads(data["variables"])

    assert variables == {"agentKey": "agent/ostorlab/nmap", "useExperimental": True}


def testAgentDetailsAPIRequest_whenCalled_queryDeclaresUseExperimentalVariable() -> None:
    """Test that the GraphQL query declares and forwards the useExperimental variable."""
    api_request = agent_details.AgentDetailsAPIRequest(agent_key="agent/ostorlab/nmap")

    query = api_request.query

    assert "$useExperimental: Boolean" in query
    assert "useExperimental: $useExperimental" in query
