"""Unit tests for Agent asset."""

import pytest

from ostorlab.agent.message import serializer
from ostorlab.assets import agent


def testAgentAssetToProto_whenSelectorIsSetAndCorrect_generatesProto():
    """Test to_proto method with correct selector."""
    asset = agent.Agent(key="agent_key", version="1.0.0")
    raw = asset.to_proto()

    assert isinstance(raw, bytes)
    unraw = serializer.deserialize("v3.asset.agent", raw)
    assert unraw.key == "agent_key"


def testAgentAssetFromDict_withStringValues_returnsExpectedObject():
    """Test Agent.from_dict() returns the expected object with string values."""
    data = {
        "key": "agent_key",
        "version": "1.0.0",
        "docker_location": "docker",
        "yaml_file_location": "yaml",
    }
    expected_agent = agent.Agent(
        key="agent_key",
        version="1.0.0",
        docker_location="docker",
        yaml_file_location="yaml",
    )

    agent_asset = agent.Agent.from_dict(data)

    assert agent_asset == expected_agent


def testAgentAssetFromDict_withBytesValues_returnsExpectedObject():
    """Test Agent.from_dict() returns the expected object with bytes values."""
    data = {
        "key": b"agent_key",
        "version": b"1.0.0",
        "docker_location": b"docker",
        "yaml_file_location": b"yaml",
    }
    expected_agent = agent.Agent(
        key="agent_key",
        version="1.0.0",
        docker_location="docker",
        yaml_file_location="yaml",
    )

    agent_asset = agent.Agent.from_dict(data)

    assert agent_asset == expected_agent


def testAgentAssetFromDict_missingKey_raisesValueError():
    """Test Agent.from_dict() raises ValueError when key is missing."""
    with pytest.raises(ValueError, match="key is missing."):
        agent.Agent.from_dict({})


def testAgentAssetFromDict_missingAllOptionalFields_returnsExpectedObject():
    """Test Agent.from_dict() returns the expected object when all optional fields are not provided."""
    data = {"key": "agent_key"}
    expected_agent = agent.Agent(key="agent_key")

    agent_asset = agent.Agent.from_dict(data)

    assert agent_asset == expected_agent
