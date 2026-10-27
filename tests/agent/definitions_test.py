"""Unittest for runtime definitions."""

import io
from typing import Any

import pytest

from ostorlab.agent import definitions
from ostorlab.agent.schema import validator
from ostorlab.utils import definitions as utils_defintions


def testAgentDefinitionFromYaml_whenYamlIsValid_returnsValidAgentDefinition() -> None:
    """Tests the creation of an agent definition from a valid yaml definition file."""
    valid_yaml_data = """
            kind: Agent
            name: "agent1"
            description: "Agent1 Description should be here"
            image: "some/path/to/the/image"
            source: "https://github.com/"
            durability: "development"
            restrictions: 
            - "restriction1"
            - "restriction2"
            in_selectors: 
            - "in_selector1"
            - "in_selector2"
            out_selectors:
            - "out_selector1"
            - "out_selector2"
            restart_policy: "any"
            args:
              - name: "template_urls"
                type: "array"
                description: "list of template urls to run."
                value:
                  - 'https://google.com'
                  - 1
              - name: "domain"
                type: "string"
        """

    yaml_data_file = io.StringIO(valid_yaml_data)

    agent_definition = definitions.AgentDefinition.from_yaml(yaml_data_file)

    assert agent_definition.name == "agent1"
    assert agent_definition.in_selectors == ["in_selector1", "in_selector2"]
    assert agent_definition.out_selectors == ["out_selector1", "out_selector2"]


def testAgentDefinitionFromYaml_withOpenPorts_correctlyParseTheSourceAndDestinationPorts() -> (
    None
):
    """Ensure the source & destination values of the open ports fields are parsed & handled correctly."""
    valid_yaml_data = """
            kind: Agent
            name: "agent42"
            description: "Agent 42, not 41."
            source: "https://github.com/"
            in_selectors: 
            - "in_selector1"
            - "in_selector2"
            out_selectors:
            - "out_selector1"
            - "out_selector2"
            args:
              - name: "template_urls"
                type: "array"
                description: "list of template urls to run."
                value:
                  - 'https://google.com'
                  - 1
            caps: [NET_ADMIN]
            open_ports:
              - src_port: 4242
                dest_port: 4242
        """

    yaml_data_file = io.StringIO(valid_yaml_data)

    agent_definition = definitions.AgentDefinition.from_yaml(yaml_data_file)

    assert agent_definition.name == "agent42"
    assert agent_definition.caps == ["NET_ADMIN"]
    assert agent_definition.open_ports == [
        utils_defintions.PortMapping(
            source_port=4242,
            destination_port=4242,
        )
    ]


def testAgentDefinitionFromYaml_withVolumes_correctlyParsesSharedScanVolumes() -> None:
    """Ensure the volumes field is parsed into Volume objects with defaults applied."""
    valid_yaml_data = """
            kind: Agent
            name: "agent42"
            description: "Agent 42, not 41."
            in_selectors:
            - "in_selector1"
            out_selectors:
            - "out_selector1"
            volumes:
              - name: "repository_code"
                path: "/code"
                read_only: false
              - name: "shared_cache"
                path: "/cache"
        """
    yaml_data_file = io.StringIO(valid_yaml_data)

    agent_definition = definitions.AgentDefinition.from_yaml(yaml_data_file)

    assert agent_definition.volumes == [
        utils_defintions.Volume(name="repository_code", path="/code", read_only=False),
        utils_defintions.Volume(name="shared_cache", path="/cache", read_only=True),
    ]


@pytest.mark.parametrize("seconds", [10, 1.5, 86400, 9223372036])
def testAgentDefinitionFromYaml_withStopGracePeriod_preservesSeconds(
    seconds: float,
) -> None:
    definition = definitions.AgentDefinition.from_yaml(
        io.StringIO(
            f"kind: Agent\nname: worker\nin_selectors: []\nout_selectors: []\nstop_grace_period: {seconds}\n"
        )
    )
    assert definition.stop_grace_period == seconds


def testAgentDefinition_withoutStopGracePeriod_defaultsToTenSeconds() -> None:
    assert definitions.AgentDefinition(name="worker").stop_grace_period == 10
    definition = definitions.AgentDefinition.from_yaml(
        io.StringIO("kind: Agent\nname: worker\nin_selectors: []\nout_selectors: []\n")
    )
    assert definition.stop_grace_period == 10


@pytest.mark.parametrize(
    "seconds",
    [0, -1, 1e-10, float("nan"), float("inf"), 9223372037, True, "86400", None],
)
def testAgentDefinition_withInvalidStopGracePeriod_rejectsValue(seconds: Any) -> None:
    with pytest.raises(ValueError, match="stop_grace_period"):
        definitions.AgentDefinition(name="worker", stop_grace_period=seconds)


@pytest.mark.parametrize(
    "seconds", ["0", "-1", "1e-10", ".inf", "9223372037", "true", '"86400"', "null"]
)
def testAgentDefinitionFromYaml_withInvalidStopGracePeriod_rejectsSchema(
    seconds: str,
) -> None:
    with pytest.raises(validator.ValidationError):
        definitions.AgentDefinition.from_yaml(
            io.StringIO(
                f"kind: Agent\nname: worker\nin_selectors: []\nout_selectors: []\nstop_grace_period: {seconds}\n"
            )
        )


def testAgentDefinitionFromYaml_withNanStopGracePeriod_rejectsNonFiniteValue() -> None:
    with pytest.raises(ValueError, match="stop_grace_period"):
        definitions.AgentDefinition.from_yaml(
            io.StringIO(
                "kind: Agent\nname: worker\nin_selectors: []\nout_selectors: []\nstop_grace_period: .nan\n"
            )
        )
