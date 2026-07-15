"""Unittest for runtime definitions."""

import io

import pytest
from pytest_mock import plugin


from ostorlab.agent.schema import validator
from ostorlab.runtimes import definitions
from ostorlab.utils import definitions as utils_definitions
from ostorlab.scanner.proto.scan._location import startAgentScan_pb2
from ostorlab.scanner.proto.assets import apk_pb2
from ostorlab.assets import android_apk as android_apk_asset
from ostorlab.assets import android_aab as android_aab_asset
from ostorlab.assets import android_store as android_store_asset
from ostorlab.assets import domain_name as domain_name_asset
from ostorlab.assets import ios_ipa as ios_ipa_asset
from ostorlab.assets import ios_store as ios_store_asset
from ostorlab.assets import ipv4 as ipv4_asset
from ostorlab.assets import link as link_asset
from ostorlab.assets import ticket as ticket_asset
from ostorlab.assets import risk as risk_asset


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
        restart_policy="",
        open_ports=[],
    )
    dummy_agent_def2 = definitions.AgentSettings(
        key="agent/ostorlab/SmallFuzzer",
        args=[utils_definitions.Arg(name="color", type="string", value="blue")],
        constraints=[],
        mounts=[],
        restart_policy="",
        open_ports=[
            utils_definitions.PortMapping(source_port=50800, destination_port=55000)
        ],
    )
    dummy_agents = [dummy_agent_def1, dummy_agent_def2]
    valid_yaml_def = io.StringIO(valid_yaml)

    agentgrp_def = definitions.AgentGroupDefinition.from_yaml(valid_yaml_def)

    assert len(agentgrp_def.agents) == len(dummy_agents)
    assert agentgrp_def.agents == dummy_agents


def testAgentGroupDefinitionFromYaml_whenServiceNameProvided_parsedCorrectly():
    """Test that service_name in YAML is parsed into AgentSettings."""
    valid_yaml = """
        kind: "AgentGroup"
        description: "test"
        agents:
          - key: "agent/ostorlab/crawler"
            service_name: "crawler_bus"
    """

    agentgrp_def = definitions.AgentGroupDefinition.from_yaml(io.StringIO(valid_yaml))

    assert agentgrp_def.agents[0].service_name == "crawler_bus"


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


def testAgentInstanceSettingsTo_whenProtoHasIntField_returnsBytes():
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
    assert new_instance.args[0].value == b'"fast"'


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


def testAgentGroupDefinitionFromNatsRequest_whenAgentArgOfTypeNumber_castsArgumentToInt() -> (
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
        name="arg1", type="number", value=42, description=None
    )
    assert isinstance(agent_group_def.agents[0].args[0].value, int) is True


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


def testAgentInstanceSettingsToRawProto_whenDepthAndCyclicLimitsAreSet_shouldSerialize():
    """Unit test to ensure that depth and cyclic processing limits are correctly serialized."""
    instance_settings = definitions.AgentSettings(
        key="agent/ostorlab/BigFuzzer",
        bus_url="mq",
        bus_exchange_topic="topic",
        bus_management_url="mq_managment",
        bus_vhost="vhost",
        args=[utils_definitions.Arg(name="speed", type="string", value="fast")],
        cyclic_processing_limit=2,
        depth_processing_limit=3,
    )

    proto = instance_settings.to_raw_proto()
    parsed_proto = instance_settings.from_proto(proto)

    assert parsed_proto.key == "agent/ostorlab/BigFuzzer"
    assert parsed_proto.cyclic_processing_limit == 2
    assert parsed_proto.depth_processing_limit == 3


def testAgentInstanceSettingsToRawProto_whenAcceptedAgentsListIsSet_shouldSerialize() -> (
    None
):
    """Unit test to ensure that accepted agents list is correctly serialized."""
    instance_settings = definitions.AgentSettings(
        key="agent/org/main_agent",
        bus_url="mq",
        bus_exchange_topic="topic",
        bus_management_url="mq_managment",
        bus_vhost="vhost",
        args=[utils_definitions.Arg(name="speed", type="string", value="fast")],
        accepted_agents=["agent1", "agent2"],
    )

    proto = instance_settings.to_raw_proto()
    parsed_proto = instance_settings.from_proto(proto)

    assert parsed_proto.key == "agent/org/main_agent"
    assert parsed_proto.accepted_agents == ["agent1", "agent2"]


def testAgentInstanceSettingsToRawProto_whenExtendedInSelectorsListIsSet_shouldSerialize() -> (
    None
):
    """Unit test to ensure that agent settings in selectors list is correctly serialized."""
    instance_settings = definitions.AgentSettings(
        key="agent/org/main_agent",
        bus_url="mq",
        bus_exchange_topic="topic",
        bus_management_url="mq_managment",
        bus_vhost="vhost",
        args=[utils_definitions.Arg(name="speed", type="string", value="fast")],
        in_selectors=["in_selector1", "in_selector2"],
    )

    proto = instance_settings.to_raw_proto()
    parsed_proto = instance_settings.from_proto(proto)

    assert parsed_proto.key == "agent/org/main_agent"
    assert parsed_proto.in_selectors == ["in_selector1", "in_selector2"]


def testAgentInstanceSettingsToRawProto_whenServiceNameIsSet_shouldSerialize() -> None:
    """Unit test to ensure that service_name is correctly serialized and deserialized."""
    instance_settings = definitions.AgentSettings(
        key="agent/org/main_agent",
        bus_url="mq",
        bus_exchange_topic="topic",
        bus_management_url="mq_managment",
        bus_vhost="vhost",
        args=[],
        service_name="instance_1",
    )

    proto = instance_settings.to_raw_proto()
    parsed_proto = instance_settings.from_proto(proto)

    assert parsed_proto.service_name == "instance_1"


def testAgentInstanceSettingsToRawProto_whenServiceNameIsNotSet_shouldDeserializeAsNone() -> (
    None
):
    """Unit test to ensure that when service_name is absent, from_proto returns None/empty."""
    instance_settings = definitions.AgentSettings(
        key="agent/org/main_agent",
        bus_url="mq",
        bus_exchange_topic="topic",
        bus_management_url="mq_managment",
        bus_vhost="vhost",
        args=[],
    )

    proto = instance_settings.to_raw_proto()
    parsed_proto = instance_settings.from_proto(proto)

    assert parsed_proto.service_name is None


def testAgentGroupDefinitionFromNatsRequest_whenAgentHasCapsAndSelectors_returnsNativePythonLists() -> (
    None
):
    """Ensure caps and in_selectors are plain Python lists, not protobuf RepeatedScalarFieldContainers."""
    msg = startAgentScan_pb2.Message(
        reference_scan_id=42,
        key="agentgroup/ostorlab/agent_group42",
        agents=[
            startAgentScan_pb2.Agent(
                key="agent/ostorlab/agent1",
                caps=["NET_ADMIN", "SYS_PTRACE"],
                in_selectors=["v3.report.vulnerability.network.port.service.http"],
            ),
        ],
        apk=apk_pb2.Message(content=b"dummy_apk"),
    )

    agent_group_def = definitions.AgentGroupDefinition.from_bus_message(msg)

    assert isinstance(agent_group_def.agents[0].caps, list) is True
    assert isinstance(agent_group_def.agents[0].in_selectors, list) is True
    assert agent_group_def.agents[0].caps == ["NET_ADMIN", "SYS_PTRACE"]
    assert agent_group_def.agents[0].in_selectors == [
        "v3.report.vulnerability.network.port.service.http"
    ]


def testAgentGroupDefinitionFromNatsRequest_whenAgentHasOpenPortsAndServiceName_parsedCorrectly() -> (
    None
):
    """Ensure open_ports and service_name are correctly parsed from a NATS message."""
    msg = startAgentScan_pb2.Message(
        reference_scan_id=42,
        key="agentgroup/ostorlab/agent_group42",
        agents=[
            startAgentScan_pb2.Agent(
                key="agent/ostorlab/proxy",
                open_ports=[
                    startAgentScan_pb2.PortMapping(src_port=56813, dest_port=56813)
                ],
                service_name="proxy_bus",
            ),
        ],
        apk=apk_pb2.Message(content=b"dummy_apk"),
    )

    agent_group_def = definitions.AgentGroupDefinition.from_bus_message(msg)

    assert agent_group_def.agents[0].open_ports == [
        utils_definitions.PortMapping(source_port=56813, destination_port=56813)
    ]
    assert agent_group_def.agents[0].service_name == "proxy_bus"


def testAssetGroupDefinitionFromYaml_whenYamlIsValid_returnsValidAssetGroupDefinition(
    mocker: plugin.MockerFixture,
):
    """Tests the creation of an asset group definition from a valid yaml definition file."""
    valid_yaml = """
description: Target group definition for the NSA
kind: targetGroup
name: master_scan
assets:
  androidStore:
      - package_name: "com.caesar.salad"
      - package_name: "test.this.schema"
  androidApkFile:
      - path: /tests/files/fake_app.apk
      - path: /tests/files/fake_app_2.apk
  androidAabFile:
      - path: /tests/files/fake_app.aab
      - path: /tests/files/fake_app_2.aab
  iosStore:
      - bundle_id: "com.caesar.salad"
      - bundle_id: "test.this.schema"
  iosFile:
      - path: /files/fake_app.ipa
      - url: https://cia.sketchy.com/secret_files.ipa
  link:
      - url: "https://cia.sketchy.com/secret_files"
        method: "GET"
      - url: "https://nasa.gov.ma/artemis_nuclear_capabilities"
        method: "POST"
  domain:
      - name: "ostor.co"
      - name: "seclab.dev"
  ip:
      - host: "10.21.11.11"
        mask: 30
      - host: 0.1.2.1
  ticket:
      - title: "Critical vulnerability"
        description: "Details go here"
        ticket_id: "T-01"
        ticket_key: "PROJ-1"
        comments:
          - author: "sec-ops"
            message: "confirmed reproduction"
"""
    mocker.patch("pathlib.Path.read_bytes", return_value=b"content")
    assets = [
        android_aab_asset.AndroidAab(
            content=b"content", path="/tests/files/fake_app.aab"
        ),
        android_aab_asset.AndroidAab(
            content=b"content", path="/tests/files/fake_app_2.aab"
        ),
        android_apk_asset.AndroidApk(
            content=b"content", path="/tests/files/fake_app.apk"
        ),
        android_apk_asset.AndroidApk(
            content=b"content", path="/tests/files/fake_app_2.apk"
        ),
        ios_ipa_asset.IOSIpa(content=b"content", path="/files/fake_app.ipa"),
        ios_ipa_asset.IOSIpa(content_url="https://cia.sketchy.com/secret_files.ipa"),
        android_store_asset.AndroidStore(package_name="com.caesar.salad"),
        android_store_asset.AndroidStore(package_name="test.this.schema"),
        ios_store_asset.IOSStore(bundle_id="com.caesar.salad"),
        ios_store_asset.IOSStore(bundle_id="test.this.schema"),
        ipv4_asset.IPv4(host="10.21.11.11", mask="30"),
        ipv4_asset.IPv4(host="0.1.2.1", mask=None),
        domain_name_asset.DomainName(name="ostor.co"),
        domain_name_asset.DomainName(name="seclab.dev"),
        link_asset.Link(url="https://cia.sketchy.com/secret_files", method="GET"),
        link_asset.Link(
            url="https://nasa.gov.ma/artemis_nuclear_capabilities", method="POST"
        ),
        ticket_asset.Ticket(
            title="Critical vulnerability",
            description="Details go here",
            ticket_id="T-01",
            ticket_key="PROJ-1",
            comments=[
                ticket_asset.Comment(author="sec-ops", message="confirmed reproduction")
            ],
        ),
    ]
    valid_yaml_def = io.StringIO(valid_yaml)

    asset_group_def = definitions.AssetsDefinition.from_yaml(valid_yaml_def)

    assert len(asset_group_def.targets) == 17
    assert assets == asset_group_def.targets


def testAssetGroupDefinitionFromYaml_whenRiskAssetsProvided_returnsRiskAssets():
    """Tests parsing a target group with multiple risk assets embedding different targets."""
    valid_yaml = """
description: Target group with risks
kind: targetGroup
name: risk_scan
assets:
  risk:
      - severity: HIGH
        description: Server exposed to the internet
        ip:
            host: "8.8.8.8"
            mask: 32
      - severity: LOW
        description: Weak TLS configuration
        domain:
            name: example.com
      - severity: MEDIUM
        description: Vulnerable APK
        androidApkFile:
            url: https://example.com/app.apk
"""
    valid_yaml_def = io.StringIO(valid_yaml)

    asset_group_def = definitions.AssetsDefinition.from_yaml(valid_yaml_def)

    assert len(asset_group_def.targets) == 3
    assert all(
        isinstance(target, risk_asset.Risk) for target in asset_group_def.targets
    )
    assert asset_group_def.targets[0].rating == "HIGH"
    assert asset_group_def.targets[0].description == "Server exposed to the internet"
    assert asset_group_def.targets[0].ipv4 == ipv4_asset.IPv4(host="8.8.8.8", mask="32")
    assert asset_group_def.targets[1].rating == "LOW"
    assert asset_group_def.targets[1].domain_name == domain_name_asset.DomainName(
        name="example.com"
    )
    assert asset_group_def.targets[2].android_apk == android_apk_asset.AndroidApk(
        content_url="https://example.com/app.apk"
    )


def testAssetGroupDefinitionFromYaml_whenRiskAssetHasMaskedIp_serializesToProto():
    """Tests that a risk embedding an ip with a numeric mask serializes to protobuf.

    The ipv4 proto mask field is a string while YAML parses the mask as an int, so
    this guards against a regression where serialization crashed with a TypeError."""
    valid_yaml = """
description: Target group with a risk
kind: targetGroup
name: risk_scan
assets:
  risk:
      - severity: CRITICAL
        description: Server exposed
        ip:
            host: "8.8.8.8"
            mask: 32
"""
    asset_group_def = definitions.AssetsDefinition.from_yaml(io.StringIO(valid_yaml))

    proto_bytes = asset_group_def.targets[0].to_proto()

    assert isinstance(proto_bytes, bytes)
    assert len(proto_bytes) > 0
    assert asset_group_def.targets[0].ipv4.mask == "32"


def testAssetGroupDefinitionFromYaml_whenRiskEmbedsMultipleTargets_raisesValidationError():
    """Tests that a risk embedding more than one target is rejected instead of silently
    dropping all but one when serialized to the proto oneof."""
    invalid_yaml = """
description: Target group with an invalid risk
kind: targetGroup
name: risk_scan
assets:
  risk:
      - severity: HIGH
        description: Server exposed
        ip:
            host: "8.8.8.8"
        domain:
            name: example.com
"""

    with pytest.raises(validator.ValidationError, match="at most one target"):
        definitions.AssetsDefinition.from_yaml(io.StringIO(invalid_yaml))


def testAssetGroupDefinitionFromYaml_whenRiskHasNoTarget_returnsTargetlessRisk():
    """Tests that a risk without an embedded target is accepted, consistent with the
    ``oxo scan run ... risk`` subcommand where target assets are optional."""
    valid_yaml = """
description: Target group with a targetless risk
kind: targetGroup
name: risk_scan
assets:
  risk:
      - severity: HIGH
        description: General exposure with no specific asset
"""

    asset_group_def = definitions.AssetsDefinition.from_yaml(io.StringIO(valid_yaml))

    assert len(asset_group_def.targets) == 1
    risk = asset_group_def.targets[0]
    assert isinstance(risk, risk_asset.Risk)
    assert risk.rating == "HIGH"
    assert risk.ipv4 is None
    assert risk.domain_name is None
    assert isinstance(risk.to_proto(), bytes)


def testAssetGroupDefinitionFromYaml_whenRiskEmbedsLink_returnsRiskWithLink():
    """Tests parsing a risk asset embedding a link target."""
    valid_yaml = """
description: Risk with link
kind: targetGroup
name: risk_scan
assets:
  risk:
      - severity: HIGH
        description: Vulnerable endpoint
        link:
            url: https://example.com/api
            method: GET
"""

    asset_group_def = definitions.AssetsDefinition.from_yaml(io.StringIO(valid_yaml))

    assert asset_group_def.targets[0].link == link_asset.Link(
        url="https://example.com/api", method="GET"
    )


def testAssetGroupDefinitionFromYaml_whenRiskEmbedsAndroidStore_returnsRiskWithAndroidStore():
    """Tests parsing a risk asset embedding an android store target."""
    valid_yaml = """
description: Risk with android store
kind: targetGroup
name: risk_scan
assets:
  risk:
      - severity: MEDIUM
        description: Risky Android app
        androidStore:
            package_name: com.example.app
"""

    asset_group_def = definitions.AssetsDefinition.from_yaml(io.StringIO(valid_yaml))

    assert asset_group_def.targets[0].android_store == android_store_asset.AndroidStore(
        package_name="com.example.app"
    )


def testAssetGroupDefinitionFromYaml_whenRiskEmbedsIosStore_returnsRiskWithIosStore():
    """Tests parsing a risk asset embedding an iOS store target."""
    valid_yaml = """
description: Risk with iOS store
kind: targetGroup
name: risk_scan
assets:
  risk:
      - severity: MEDIUM
        description: Risky iOS app
        iosStore:
            bundle_id: com.example.app
"""

    asset_group_def = definitions.AssetsDefinition.from_yaml(io.StringIO(valid_yaml))

    assert asset_group_def.targets[0].ios_store == ios_store_asset.IOSStore(
        bundle_id="com.example.app"
    )


def testAssetGroupDefinitionFromYaml_whenRiskEmbedsAndroidAabFile_returnsRiskWithAab(
    mocker: plugin.MockerFixture,
):
    """Tests parsing a risk asset embedding an Android AAB file by local path."""
    mocker.patch("pathlib.Path.read_bytes", return_value=b"aab content")
    valid_yaml = """
description: Risk with android aab
kind: targetGroup
name: risk_scan
assets:
  risk:
      - severity: HIGH
        description: Vulnerable AAB
        androidAabFile:
            path: /app.aab
"""

    asset_group_def = definitions.AssetsDefinition.from_yaml(io.StringIO(valid_yaml))

    assert asset_group_def.targets[0].android_aab == android_aab_asset.AndroidAab(
        content=b"aab content", path="/app.aab"
    )


def testAssetGroupDefinitionFromYaml_whenRiskIosFileHasLocalPath_readsContent(
    mocker: plugin.MockerFixture,
):
    """Tests that a risk embedding an iOS file by local path is read, guarding the
    schema key which must be `path` (singular) to match the parser."""
    mocker.patch("pathlib.Path.read_bytes", return_value=b"ipa content")
    valid_yaml = """
description: Target group with an iOS risk
kind: targetGroup
name: risk_scan
assets:
  risk:
      - severity: HIGH
        description: Vulnerable IPA
        iosFile:
            path: /app.ipa
"""

    asset_group_def = definitions.AssetsDefinition.from_yaml(io.StringIO(valid_yaml))

    risk = asset_group_def.targets[0]
    assert risk.ios_ipa == ios_ipa_asset.IOSIpa(content=b"ipa content", path="/app.ipa")


def testAssetGroupDefinitionFromYaml_whenRiskIpInvalid_raisesValidationError():
    """Tests that a risk embedding an invalid ip is rejected instead of silently
    producing a risk with no target."""
    invalid_yaml = """
description: Target group with an invalid risk ip
kind: targetGroup
name: risk_scan
assets:
  risk:
      - severity: HIGH
        description: Server exposed
        ip:
            host: not-an-ip
"""

    with pytest.raises(validator.ValidationError, match="invalid IP address"):
        definitions.AssetsDefinition.from_yaml(io.StringIO(invalid_yaml))


def testAssetGroupDefinitionFromYaml_whenRiskFileAssetEmpty_raisesValidationError():
    """Tests that a risk embedding a file asset with neither path nor url is rejected
    instead of producing an empty asset."""
    invalid_yaml = """
description: Target group with an empty risk file asset
kind: targetGroup
name: risk_scan
assets:
  risk:
      - severity: HIGH
        description: Vulnerable APK
        androidApkFile: {}
"""

    with pytest.raises(validator.ValidationError, match="requires either a valid path"):
        definitions.AssetsDefinition.from_yaml(io.StringIO(invalid_yaml))


@pytest.mark.parametrize(
    "target_key, missing_field",
    [
        ("domain", "name"),
        ("link", "url"),
        ("androidStore", "package_name"),
        ("iosStore", "bundle_id"),
    ],
)
def testAssetGroupDefinitionFromYaml_whenRiskTargetIsEmpty_raisesValidationError(
    target_key: str, missing_field: str
) -> None:
    """Tests that a risk embedding a target with no identifying field is rejected.

    The target sub-schemas mark no field as required, so an empty entry would
    otherwise build a target that is silently dropped from the proto oneof."""
    invalid_yaml = f"""
description: Target group with an empty risk target
kind: targetGroup
name: risk_scan
assets:
  risk:
      - severity: HIGH
        description: Server exposed
        {target_key}: {{}}
"""

    with pytest.raises(
        validator.ValidationError,
        match=f"Risk {target_key} requires a {missing_field}.",
    ):
        definitions.AssetsDefinition.from_yaml(io.StringIO(invalid_yaml))


@pytest.mark.parametrize(
    "target_key, blank_field",
    [
        ("domain", "name"),
        ("link", "url"),
        ("androidStore", "package_name"),
        ("iosStore", "bundle_id"),
    ],
)
def testAssetGroupDefinitionFromYaml_whenRiskTargetFieldBlank_raisesValidationError(
    target_key: str, blank_field: str
) -> None:
    """Tests that a risk target whose identifying field is an empty string is rejected.

    The sub-schemas set no ``minLength``, so a blank value passes schema validation
    and would otherwise build a target serialized as an empty proto oneof."""
    invalid_yaml = f"""
description: Target group with a blank risk target field
kind: targetGroup
name: risk_scan
assets:
  risk:
      - severity: HIGH
        description: Server exposed
        {target_key}:
            {blank_field}: ""
"""

    with pytest.raises(
        validator.ValidationError,
        match=f"Risk {target_key} requires a {blank_field}.",
    ):
        definitions.AssetsDefinition.from_yaml(io.StringIO(invalid_yaml))


def testAssetGroupDefinitionFromYaml_whenRiskLinkHasNoMethod_defaultsToGet():
    """Tests that a risk link without a method defaults to GET, matching the CLI.

    The ``risk`` CLI defaults ``--link-method`` to GET, so a link ported to YAML
    without a method should behave the same rather than being rejected."""
    yaml_definition = """
description: Target group with a link missing its method
kind: targetGroup
name: risk_scan
assets:
  risk:
      - severity: HIGH
        description: Vulnerable endpoint
        link:
            url: https://example.com/api
"""

    asset_group_def = definitions.AssetsDefinition.from_yaml(
        io.StringIO(yaml_definition)
    )

    assert asset_group_def.targets[0].link == link_asset.Link(
        url="https://example.com/api", method="GET"
    )


def testAssetGroupDefinitionFromYaml_whenRiskSeverityInvalid_raisesValidationError():
    """Tests that an invalid risk severity is rejected by schema validation."""
    invalid_yaml = """
description: Target group with an invalid risk
kind: targetGroup
name: risk_scan
assets:
  risk:
      - severity: NOT_A_SEVERITY
        description: Server exposed
"""

    with pytest.raises(validator.ValidationError):
        definitions.AssetsDefinition.from_yaml(io.StringIO(invalid_yaml))
