"""Unit tests for customized click types."""

import pytest
import click

from ostorlab.cli import types


@pytest.mark.parametrize(
    "input_value, expected_output",
    [
        ("nmap", "agent/ostorlab/nmap"),
        ("@dev/nmap", "agent/dev/nmap"),
        ("agent/test/nmap", "agent/test/nmap"),
    ],
)
def testAgentKeyTypeConversion_whenValidInputReceived_returnCorrectKey(
    input_value: str, expected_output: str
) -> None:
    agent_type = types.AgentKeyType()

    result = agent_type.convert(input_value, None, None)

    assert result == expected_output


@pytest.mark.parametrize(
    "input_value", ["/nmap", "@agent/ostorlab/nmap/", "agent/ostorlab/nmap/"]
)
def testAgentKeyTypeConversion_whenInValidInputReceived_raiseBadParameter(
    input_value: str,
) -> None:
    agent_type = types.AgentKeyType()

    with pytest.raises(click.BadParameter):
        agent_type.convert(input_value, None, None)
