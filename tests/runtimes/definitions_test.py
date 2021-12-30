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


def testAgentGroupDefinitionFromYaml_whenYamlIsValid_returnsValidAgentGroupDefinition():
    """Tests the creation of an agent group definition from a valid yaml definition file."""
    valid_yaml = """
        kind: "AgentGroup1"
        description: "AgentGroup1 Should be here"
        image: "some/path/to/the/image"
        restart_policy: "always_restart"
        agents:
          - name: "AgentBigFuzzer"
            constraints:
              - "constraint1"
              - "constraint2"
            mounts:
              - "mount1"
              - "mount2"
            restart_policy: "always_restart"
            open_ports:
                src_port: 50000
                dest_port: 50300
            args:
                color: "red"
                speed: "slow" 
          - name: "AgentSmallFuzzer"
            constraints:
              - "constraint3"
              - "constraint4"
            mounts:
              - "mount3"
              - "mount4"
            restart_policy: "always_restart"
            replicas: 1
            open_ports:
                src_port: 50800
                dest_port: 55000
            args:
                color: "blue"
                speed: "fast" 
    """
    dummy_agent_def1 = definitions.AgentDefinition(
        name='AgentBigFuzzer',
        args={'color': 'red', 'speed': 'slow'},
        constraints=['constraint1', 'constraint2'],
        mounts=['mount1', 'mount2'],
        restart_policy='always_restart',
        open_ports={'src_port': 50000, 'dest_port': 50300},
    )
    dummy_agent_def2 = definitions.AgentDefinition(
        name='AgentSmallFuzzer',
        args={'color': 'blue', 'speed': 'fast'},
        constraints=['constraint3', 'constraint4'],
        mounts=['mount3', 'mount4'],
        restart_policy='always_restart',
        open_ports={'src_port': 50800, 'dest_port': 55000},
    )
    dummy_agents = [dummy_agent_def1, dummy_agent_def2]


    agentgrp_def_object = definitions.AgentGroupDefinition([])
    valid_yaml_def = io.StringIO(valid_yaml)

    agentgrp_def = agentgrp_def_object.from_yaml(valid_yaml_def)

    assert len(agentgrp_def.agents) == len(dummy_agents)
    assert agentgrp_def.agents == dummy_agents


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
