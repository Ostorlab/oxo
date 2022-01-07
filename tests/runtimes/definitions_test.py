"""Unittest for runtime definitions."""
import io

from ostorlab.runtimes import definitions
from ostorlab.utils import defintions as utils_definitions


def testAgentGroupDefinitionFromYaml_whenYamlIsValid_returnsValidAgentGroupDefinition():
    """Tests the creation of an agent group definition from a valid yaml definition file."""
    valid_yaml = """
        kind: "AgentGroup"
        description: "AgentGroup1 Should be here"
        image: "some/path/to/the/image"
        restart_policy: "always_restart"
        agents:
          - key: "agent/ostorlab/BigFuzzer"
            constraints:
              - "constraint1"
              - "constraint2"
            in_selectors: 
              - "in_selector1"
              - "in_selector2"
            out_selectors:
              - "out_selector1"
              - "out_selector2"  
            mounts:
              - "mount1"
              - "mount2"
            restart_policy: "always_restart"
            open_ports:
                - src_port: 50000
                  dest_port: 50300
            args:
              - name: "color"
                type: "string"
                value: "red"
          - key: "agent/ostorlab/SmallFuzzer"
            constraints:
              - "constraint3"
              - "constraint4"
            in_selectors: 
              - "in_selector3"
              - "in_selector4"
            out_selectors:
              - "out_selector3"
              - "out_selector4"
            mounts:
              - "mount3"
              - "mount4"
            restart_policy: "always_restart"
            replicas: 1
            open_ports:
                - src_port: 50800
                  dest_port: 55000
            args:
              - name: "color"
                type: "string"
                value: "blue"
    """
    dummy_agent_def1 = definitions.AgentSettings(
        key='agent/ostorlab/BigFuzzer',
        args=[utils_definitions.Arg(name='color', type='string', value='red')],
        constraints=['constraint1', 'constraint2'],
        mounts=['mount1', 'mount2'],
        restart_policy='always_restart',
        open_ports=[utils_definitions.PortMapping(source_port=50000, destination_port=50300)],
    )
    dummy_agent_def2 = definitions.AgentSettings(
        key='agent/ostorlab/SmallFuzzer',
        args=[utils_definitions.Arg(name='color', type='string', value='blue')],
        constraints=['constraint3', 'constraint4'],
        mounts=['mount3', 'mount4'],
        restart_policy='always_restart',
        open_ports=[utils_definitions.PortMapping(source_port=50800, destination_port=55000)],
    )
    dummy_agents = [dummy_agent_def1, dummy_agent_def2]
    valid_yaml_def = io.StringIO(valid_yaml)

    agentgrp_def = definitions.AgentGroupDefinition.from_yaml(valid_yaml_def)

    assert len(agentgrp_def.agents) == len(dummy_agents)
    assert agentgrp_def.agents == dummy_agents


def testAgentInstanceSettingsTo_whenProtoIsValid_returnsBytes():
    """Tests that the generated proto is of type bytes."""
    instance_settings = definitions.AgentSettings(
        key='agent/ostorlab/BigFuzzer',
        bus_url='mq',
        bus_exchange_topic='topic',
        bus_managment_url='mq_managment',
        bus_vhost='vhost',
        args=[utils_definitions.Arg(name='speed', type='str', value=b'fast')]
    )

    proto = instance_settings.to_raw_proto()

    assert isinstance(proto, bytes)


def testAgentInstanceSettingsFromProto_whenProtoIsValid_returnsValidAgentInstanceSettings():
    """Uses two-way generation and parsing to ensure the passed attributes are recreated."""
    instance_settings = definitions.AgentSettings(
        key='agent/ostorlab/BigFuzzer',
        bus_url='mq',
        bus_exchange_topic='topic',
        bus_managment_url='mq_managment',
        bus_vhost='vhost',
        args=[utils_definitions.Arg(name='speed', type='str', value=b'fast')]
    )

    proto = instance_settings.to_raw_proto()
    new_instance = definitions.AgentSettings.from_proto(proto)

    assert new_instance.bus_url == 'mq'
    assert new_instance.bus_exchange_topic == 'topic'
    assert len(new_instance.args) == 1
