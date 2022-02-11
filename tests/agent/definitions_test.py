"""Unittest for runtime definitions."""
import io

from ostorlab.agent import definitions


def testAgentDefinitionFromYaml_whenYamlIsValid_returnsValidAgentDefinition():
    """Tests the creation of an agent definition from a valid yaml definition file."""
    valid_yaml_data = """
            ssss
        """

    yaml_data_file = io.StringIO(valid_yaml_data)

    agent_definition = definitions.AgentDefinition.from_yaml(yaml_data_file)

    assert agent_definition.name == 'agent1'
    assert agent_definition.in_selectors == ['in_selector1', 'in_selector2']
    assert agent_definition.out_selectors == ['out_selector1', 'out_selector2']

