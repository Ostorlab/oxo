"""Unittests for the agent release channels."""

import json

import pytest

from ostorlab.agent.schema import loader
from ostorlab.utils import release_channel


@pytest.mark.parametrize(
    "channel", ["stable", "beta", "qa1", "nightly-build", "a", "a" * 32]
)
def testIsValid_whenChannelMatchesPattern_returnsTrue(channel: str) -> None:
    """Test that valid release channel names, including stable, are accepted."""
    assert release_channel.is_valid(channel) is True


@pytest.mark.parametrize(
    "channel", ["", "Beta", "1beta", "-beta", "beta.2", "beta_2", "a" * 33, "beta\n"]
)
def testIsValid_whenChannelDoesNotMatchPattern_returnsFalse(channel: str) -> None:
    """Test that names outside the release channel pattern are rejected."""
    assert release_channel.is_valid(channel) is False


def testChannelPattern_always_matchesAgentGroupSchemaPattern() -> None:
    """Test that the agent group schema validates channels with the same pattern."""
    with open(loader.AGENT_GROUP_SPEC_PATH, "r") as schema_file:
        schema = json.load(schema_file)

    schema_pattern = schema["properties"]["experimental_channel"]["pattern"]

    assert schema_pattern == release_channel.CHANNEL_PATTERN.pattern
