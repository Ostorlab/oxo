"""Tests for agent download token API request."""

import json

from ostorlab.apis import agent_download_token


def testAgentDownloadTokenAPIRequest_whenCalledWithoutVersion_createsCorrectMutation() -> (
    None
):
    """Verify the mutation is correctly formed without version."""
    request = agent_download_token.AgentDownloadTokenAPIRequest("agent/ot1/bigFuzzer")

    assert "mutation GenerateAgentImageDownloadToken" in request.query
    assert "$agentKey: String!" in request.query
    assert "$version: String" in request.query
    assert "generateAgentImageDownloadToken" in request.query
    assert "token" in request.query

    data = request.data
    assert "query" in data
    assert "variables" in data

    variables = json.loads(data["variables"])
    assert variables["agentKey"] == "agent/ot1/bigFuzzer"
    assert variables["version"] is None


def testAgentDownloadTokenAPIRequest_whenCalledWithVersion_encodesVersionCorrectly() -> (
    None
):
    """Verify the mutation encodes the version argument correctly."""
    request = agent_download_token.AgentDownloadTokenAPIRequest(
        "agent/ot1/bigFuzzer", version="1.2.3"
    )

    data = request.data
    variables = json.loads(data["variables"])
    assert variables["agentKey"] == "agent/ot1/bigFuzzer"
    assert variables["version"] == "1.2.3"
