"""Unittest for runtime definitions."""

import io

from ostorlab.agent import definitions
from ostorlab.utils import definitions as utils_defintions


def testAgentDefinitionFromYaml_whenYamlIsValid_returnsValidAgentDefinition():
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
