"""Unittest for runtime definitions."""
import io

from ostorlab.runtimes import definitions


def testAgentDefinitionFromYaml_whenYamlIsValid_returnsValidAgentDefinition():
    """Tests the creation of an agent definition from a valid yaml definition file."""
    valid_yaml_data = """
            name: "Agent1"
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
            restart_policy: "run_once"
        """

    yaml_data_file = io.StringIO(valid_yaml_data)

    agent_definition = definitions.AgentDefinition.from_yaml(yaml_data_file)

    assert agent_definition.name == 'Agent1'
    assert agent_definition.in_selectors == ['in_selector1', 'in_selector2']
    assert agent_definition.out_selectors == ['out_selector1', 'out_selector2']


def testAgentInstanceSettingsTo_whenProtoIsValid_returnsBytes():
    """Tests that the generated proto is of type bytes."""
    instance_settings = definitions.AgentInstanceSettings(
        bus_url='mq',
        bus_exchange_topic='topic',
        args=[definitions.Arg(name='speed', type='str', value=b'fast')]
    )

    proto = instance_settings.to_raw_proto()

    assert isinstance(proto, bytes)


def testAgentInstanceSettingsFromProto_whenProtoIsValid_returnsValidAgentInstanceSettings():
    """Uses two-way generation and parsing to ensure the passed attributes are recreated."""
    instance_settings = definitions.AgentInstanceSettings(
        bus_url='mq',
        bus_exchange_topic='topic',
        args=[definitions.Arg(name='speed', type='str', value=b'fast')]
    )

    proto = instance_settings.to_raw_proto()
    new_instance = definitions.AgentInstanceSettings.from_proto(proto)

    assert new_instance.bus_url == 'mq'
    assert new_instance.bus_exchange_topic == 'topic'
    assert len(new_instance.args) == 1
