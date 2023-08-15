"""Unittest for runtime definitions."""
import io

from ostorlab.runtimes import definitions
from ostorlab.utils import defintions as utils_definitions
from ostorlab.scanner.proto.scan._location import startAgentScan_pb2
from ostorlab.scanner.proto.assets import apk_pb2


def testAgentGroupDefinitionFromYaml_whenYamlIsValid_returnsValidAgentGroupDefinition():
    """Tests the creation of an agent group definition from a valid yaml definition file."""
    valid_yaml = """
        kind: "AgentGroup"
        description: "AgentGroup1 Should be here"
        image: "some/path/to/the/image"
        agents:
          - key: "agent/ostorlab/BigFuzzer"
            args:
              - name: "color"
                type: "string"
                value: "red"
          - key: "agent/ostorlab/SmallFuzzer"
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
        key="agent/ostorlab/BigFuzzer",
        args=[utils_definitions.Arg(name="color", type="string", value="red")],
        constraints=[],
        mounts=[],
        restart_policy="any",
        open_ports=[],
    )
    dummy_agent_def2 = definitions.AgentSettings(
        key="agent/ostorlab/SmallFuzzer",
        args=[utils_definitions.Arg(name="color", type="string", value="blue")],
        constraints=[],
        mounts=[],
        restart_policy="any",
        open_ports=[
            utils_definitions.PortMapping(source_port=50800, destination_port=55000)
        ],
    )
    dummy_agents = [dummy_agent_def1, dummy_agent_def2]
    valid_yaml_def = io.StringIO(valid_yaml)

    agentgrp_def = definitions.AgentGroupDefinition.from_yaml(valid_yaml_def)

    assert len(agentgrp_def.agents) == len(dummy_agents)
    assert agentgrp_def.agents == dummy_agents


def testAgentInstanceSettingsTo_whenProtoIsValid_returnsBytes():
    """Tests that the generated proto is of type bytes."""
    instance_settings = definitions.AgentSettings(
        key="agent/ostorlab/BigFuzzer",
        bus_url="mq",
        bus_exchange_topic="topic",
        bus_management_url="mq_managment",
        bus_vhost="vhost",
        args=[utils_definitions.Arg(name="speed", type="string", value="fast")],
    )

    proto = instance_settings.to_raw_proto()

    assert isinstance(proto, bytes)


def testAgentInstanceSettingsTo_whenProtoHasNumberField_returnsBytes():
    """Test supported serializing int number."""
    instance_settings = definitions.AgentSettings(
        key="agent/ostorlab/BigFuzzer",
        bus_url="mq",
        bus_exchange_topic="topic",
        bus_management_url="mq_managment",
        bus_vhost="vhost",
        args=[utils_definitions.Arg(name="speed", type="number", value=1)],
    )

    proto = instance_settings.to_raw_proto()

    assert isinstance(proto, bytes)


def testAgentInstanceSettingsTo_whenProtoHasFloatField_returnsBytes():
    """Test supported serializing float number."""
    instance_settings = definitions.AgentSettings(
        key="agent/ostorlab/BigFuzzer",
        bus_url="mq",
        bus_exchange_topic="topic",
        bus_management_url="mq_managment",
        bus_vhost="vhost",
        args=[utils_definitions.Arg(name="speed", type="number", value=1.1)],
    )

    proto = instance_settings.to_raw_proto()

    assert isinstance(proto, bytes)


def testAgentInstanceSettingsTo_whenProtoHasBytesField_returnsBytes():
    """Test supported serializing bytes."""
    instance_settings = definitions.AgentSettings(
        key="agent/ostorlab/BigFuzzer",
        bus_url="mq",
        bus_exchange_topic="topic",
        bus_management_url="mq_managment",
        bus_vhost="vhost",
        args=[utils_definitions.Arg(name="speed", type="string", value="test")],
    )

    proto = instance_settings.to_raw_proto()

    assert isinstance(proto, bytes)


def testAgentInstanceSettingsFromProto_whenProtoIsValid_returnsValidAgentInstanceSettings():
    """Uses two-way generation and parsing to ensure the passed attributes are recreated."""
    instance_settings = definitions.AgentSettings(
        key="agent/ostorlab/BigFuzzer",
        bus_url="mq",
        bus_exchange_topic="topic",
        bus_management_url="mq_managment",
        bus_vhost="vhost",
        args=[utils_definitions.Arg(name="speed", type="string", value="fast")],
    )

    proto = instance_settings.to_raw_proto()
    new_instance = definitions.AgentSettings.from_proto(proto)

    assert new_instance.bus_url == "mq"
    assert new_instance.bus_exchange_topic == "topic"
    assert len(new_instance.args) == 1


def testAgentInstanceContainerImage_ifNoImageIsPresent_raiseValueError():
    """Uses two-way generation and parsing to ensure the passed attributes are recreated."""
    instance_settings = definitions.AgentSettings(
        key="agent/ostorlab/BigFuzzer",
        bus_url="mq",
        bus_exchange_topic="topic",
        bus_management_url="mq_managment",
        bus_vhost="vhost",
        args=[utils_definitions.Arg(name="speed", type="string", value="fast")],
    )

    assert instance_settings.container_image is None


def testAgentGroupDefinitionFromNatsRequest_always_returnsValidAgentGroupDefinition(
    start_agent_scan_nats_request: startAgentScan_pb2.Message,
) -> None:
    """Ensure the correct creation of the AgentGroupDefinition instance from a received NATs message."""

    agent_group_def = definitions.AgentGroupDefinition.from_bus_message(
        start_agent_scan_nats_request
    )

    assert agent_group_def.name == "agent_group42"
    assert len(agent_group_def.agents) == 2

    assert agent_group_def.agents[0].key == "agent/ostorlab/agent1"
    assert agent_group_def.agents[0].version == "0.0.1"
    assert agent_group_def.agents[0].replicas == 42
    assert agent_group_def.agents[0].args[0] == utils_definitions.Arg(
        name="arg1", type="number", value=42.0, description=None
    )

    assert agent_group_def.agents[1].key == "agent/ostorlab/agent2"
    assert agent_group_def.agents[1].version == "0.0.2"
    assert agent_group_def.agents[1].replicas == 1
    assert agent_group_def.agents[1].args == []


def testAgentGroupDefinitionFromNatsRequest_whenAgentArgOfTypeNumber_castsArgumentToFloat() -> (
    None
):
    """Ensure the agent argument, received as bytes, are casted to their corresponding type: Case of numbers."""
    msg = startAgentScan_pb2.Message(
        reference_scan_id=42,
        key="agentgroup/ostorlab/agent_group42",
        agents=[
            startAgentScan_pb2.Agent(
                key="agent/ostorlab/agent1",
                args=[startAgentScan_pb2.Arg(name="arg1", type="number", value=b"42")],
            ),
        ],
        apk=apk_pb2.Message(content=b"dummy_apk"),
    )

    agent_group_def = definitions.AgentGroupDefinition.from_bus_message(msg)

    assert agent_group_def.name == "agent_group42"
    assert agent_group_def.agents[0].args[0] == utils_definitions.Arg(
        name="arg1", type="number", value=42.0, description=None
    )
    assert isinstance(agent_group_def.agents[0].args[0].value, float) is True


def testAgentGroupDefinitionFromNatsRequest_whenAgentArgOfTypeString_castsArgumentToString() -> (
    None
):
    """Ensure the agent argument, received as bytes, are casted to their corresponding type: Case of strings."""
    msg = startAgentScan_pb2.Message(
        reference_scan_id=42,
        key="agentgroup/ostorlab/agent_group42",
        agents=[
            startAgentScan_pb2.Agent(
                key="agent/ostorlab/agent1",
                args=[startAgentScan_pb2.Arg(name="arg1", type="string", value=b"42")],
            ),
        ],
        apk=apk_pb2.Message(content=b"dummy_apk"),
    )

    agent_group_def = definitions.AgentGroupDefinition.from_bus_message(msg)

    assert agent_group_def.name == "agent_group42"
    assert agent_group_def.agents[0].args[0] == utils_definitions.Arg(
        name="arg1", type="string", value="42", description=None
    )
    assert isinstance(agent_group_def.agents[0].args[0].value, str) is True


def testAgentGroupDefinitionFromNatsRequest_whenAgentArgOfTypeBool_castsArgumentToBoolean() -> (
    None
):
    """Ensure the agent argument, received as bytes, are casted to their corresponding type: Case of booleans."""
    msg = startAgentScan_pb2.Message(
        reference_scan_id=42,
        key="agentgroup/ostorlab/agent_group42",
        agents=[
            startAgentScan_pb2.Agent(
                key="agent/ostorlab/agent1",
                args=[
                    startAgentScan_pb2.Arg(name="arg1", type="boolean", value=b"True")
                ],
            ),
        ],
        apk=apk_pb2.Message(content=b"dummy_apk"),
    )

    agent_group_def = definitions.AgentGroupDefinition.from_bus_message(msg)

    assert agent_group_def.name == "agent_group42"
    assert agent_group_def.agents[0].args[0] == utils_definitions.Arg(
        name="arg1", type="boolean", value=True, description=None
    )
    assert isinstance(agent_group_def.agents[0].args[0].value, bool) is True


def testAgentGroupDefinitionFromNatsRequest_whenAgentArgOfTypeArray_castsArgumentAndItsElementsToRespectiveTypes() -> (
    None
):
    """Ensure the agent argument, received as bytes, are casted to their corresponding type: Case of nested arrays."""
    msg = startAgentScan_pb2.Message(
        reference_scan_id=42,
        key="agentgroup/ostorlab/agent_group42",
        agents=[
            startAgentScan_pb2.Agent(
                key="agent/ostorlab/agent1",
                args=[
                    startAgentScan_pb2.Arg(
                        name="arg1", type="array", value=b'["value1", "value2", 3]'
                    )
                ],
            ),
        ],
        apk=apk_pb2.Message(content=b"dummy_apk"),
    )

    agent_group_def = definitions.AgentGroupDefinition.from_bus_message(msg)

    assert agent_group_def.name == "agent_group42"
    casted_argument = agent_group_def.agents[0].args[0]
    assert casted_argument == utils_definitions.Arg(
        name="arg1", type="array", value=["value1", "value2", 3], description=None
    )
    assert isinstance(casted_argument.value, list) is True
    assert isinstance(casted_argument.value[0], str) is True
    assert isinstance(casted_argument.value[1], str) is True
    assert isinstance(casted_argument.value[2], int) is True
