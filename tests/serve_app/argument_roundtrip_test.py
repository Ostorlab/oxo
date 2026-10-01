"""Argument transport, persistence, and execution roundtrip regressions."""

import io
import json
import struct
from typing import Any
from typing import Optional

import pytest
import ubjson
from flask import testing
from pytest_mock import plugin
from ruamel import yaml

from ostorlab.runtimes import definitions
from ostorlab.runtimes.cloud import runtime as cloud_runtime
from ostorlab.runtimes.local.models import models
from ostorlab.serve_app import oxo
from ostorlab.serve_app import types

ARGUMENT_CASES = [
    ("number", 80, struct.pack("d", 80)),
    ("int", 80, struct.pack("d", 80)),
    ("number", 12.5, struct.pack("d", 12.5)),
    ("number", 12345678, struct.pack("d", 12345678)),
    ("boolean", True, b"\x01"),
    ("boolean", False, b"\x00"),
    ("bool", True, b"\x01"),
    ("bool", False, b"\x00"),
    ("string", "é مرحبا 😀", "é مرحبا 😀".encode()),
    ("array", [1, "é", False], json.dumps([1, "é", False]).encode()),
    ("object", {"nested": [1, True]}, json.dumps({"nested": [1, True]}).encode()),
    ("number", None, None),
]


@pytest.mark.parametrize("transport", ["json", "cloud"])
@pytest.mark.parametrize("argument_type,value,stored_bytes", ARGUMENT_CASES)
def testPublishAndRun_withTypedArgument_preservesStorageAndExecutionValue(
    authenticated_flask_client: testing.FlaskClient,
    mocker: plugin.MockerFixture,
    scan: models.Scan,
    argument_type: str,
    value: Any,
    stored_bytes: Optional[bytes],
    transport: str,
) -> None:
    """Publish native or API text values and pass decoded arguments to execution."""
    input_value = (
        cloud_runtime.CloudRuntime()._to_serialized(value)
        if transport == "cloud"
        else value
    )
    _publish_and_run(
        authenticated_flask_client,
        mocker,
        scan,
        argument_type,
        input_value,
        value,
        stored_bytes,
        transport,
    )


@pytest.mark.parametrize(
    "argument_type,input_value,value,stored_bytes",
    [
        ("number", b"1.25e2", 125.0, struct.pack("d", 125.0)),
        ("number", b"12.5", 12.5, struct.pack("d", 12.5)),
        ("binary", b"\xff\x00\x80opaque", b"\xff\x00\x80opaque", b"\xff\x00\x80opaque"),
        ("type1", b"value1", b"value1", b"value1"),
        ("binary", b"12345678", b"12345678", b"12345678"),
        ("binary", "ÿ\x00", b"\xff\x00", b"\xff\x00"),
        ("binary", None, None, None),
    ],
)
def testPublishAndRun_withTextOrOpaqueArgument_preservesDeclaredValue(
    authenticated_flask_client: testing.FlaskClient,
    mocker: plugin.MockerFixture,
    scan: models.Scan,
    argument_type: str,
    input_value: Any,
    value: Any,
    stored_bytes: Optional[bytes],
) -> None:
    """Text numbers are parsed while binary and unknown bytes stay opaque."""
    _publish_and_run(
        authenticated_flask_client,
        mocker,
        scan,
        argument_type,
        input_value,
        value,
        stored_bytes,
        "cloud",
    )


def _publish_and_run(
    client: testing.FlaskClient,
    mocker: plugin.MockerFixture,
    scan: models.Scan,
    argument_type: str,
    input_value: Any,
    value: Any,
    stored_bytes: Optional[bytes],
    transport: str,
) -> None:
    query = """
        mutation Publish($agentGroup: OxoAgentGroupCreateInputType!) {
            publishAgentGroup(agentGroup: $agentGroup) {
                agentGroup {
                    id
                    agents { agents { args { args { name type value } } } }
                }
            }
        }
    """
    payload = {
        "query": query,
        "variables": {
            "agentGroup": {
                "description": "typed arguments",
                "agents": [
                    {
                        "key": "agent/ostorlab/test",
                        "args": [
                            {
                                "name": "value",
                                "type": argument_type,
                                "value": input_value,
                            }
                        ],
                    }
                ],
            }
        },
    }
    if transport == "json":
        response = client.post(
            "/graphql", json=payload, headers={"Accept": "application/ubjson"}
        )
    else:
        response = client.post(
            "/graphql",
            data=ubjson.dumpb(payload),
            headers={
                "Content-Type": "application/ubjson",
                "Accept": "application/ubjson",
            },
        )
    result = ubjson.loadb(response.data)
    assert response.status_code == 200, result
    assert "errors" not in result, result
    group = result["data"]["publishAgentGroup"]["agentGroup"]
    assert group["agents"]["agents"][0]["args"]["args"][0]["value"] == stored_bytes
    with models.Database() as session:
        stored_argument = session.query(models.AgentArgument).one()
        assert stored_argument.value == stored_bytes
        assert (
            models.AgentArgument.from_bytes(argument_type, stored_argument.value)
            == value
        )

    asset = models.Network.create(networks=[{"host": "192.0.2.1", "mask": "32"}])
    runtime_mock = mocker.patch(
        "ostorlab.serve_app.oxo.runtime.LocalRuntime", autospec=True
    )
    runtime_mock.return_value.prepare_scan.return_value = scan
    thread_mock = mocker.patch("ostorlab.serve_app.oxo.threading.Thread", autospec=True)
    response = client.post(
        "/graphql",
        json={
            "query": """
                mutation Run($scan: OxoAgentScanInputType!) {
                    runScan(scan: $scan) { scan { id } }
                }
            """,
            "variables": {
                "scan": {"assetIds": [asset.id], "agentGroupId": int(group["id"])}
            },
        },
    )
    result = response.get_json()
    assert "errors" not in result, result
    assert result["data"]["runScan"]["scan"]["id"] == str(scan.id)
    thread_mock.return_value.start.assert_called_once()
    prepared_argument = thread_mock.call_args.kwargs["args"][1].agents[0].args[0]
    assert prepared_argument.value == value
    if isinstance(value, bool) is True:
        assert prepared_argument.value is value


@pytest.mark.parametrize(
    "argument_type,value,stored_bytes",
    [case for case in ARGUMENT_CASES if case[0] not in ("bool", "int")],
)
def testAgentGroup_withYamlArgument_preservesCreateReadPrepareAndExport(
    argument_type: str, value: Any, stored_bytes: Optional[bytes]
) -> None:
    """YAML values retain the established database encoding and export value."""
    yaml_codec = yaml.YAML(typ="safe")
    yaml_file = io.StringIO()
    argument = {"name": "value", "type": argument_type, "description": "typed value"}
    if value is not None:
        argument["value"] = value
    yaml_codec.dump(
        {
            "kind": "AgentGroup",
            "description": "typed arguments",
            "agents": [
                {
                    "key": "agent/ostorlab/test",
                    "args": [argument],
                }
            ],
        },
        yaml_file,
    )
    yaml_file.seek(0)
    definition = definitions.AgentGroupDefinition.from_yaml(yaml_file)
    group = models.AgentGroup.create_from_agent_group_definition(definition)
    with models.Database() as session:
        assert session.query(models.AgentArgument).one().value == stored_bytes
    prepared_argument = (
        oxo.RunScanMutation._prepare_agent_group(group.id).agents[0].args[0]
    )
    assert prepared_argument.value == value
    if isinstance(value, bool) is True:
        assert prepared_argument.value is value
    exported_yaml = types.OxoAgentGroupType.resolve_yaml_source(group, None)
    exported_definition = definitions.AgentGroupDefinition.from_yaml(
        io.StringIO(exported_yaml)
    )
    assert exported_definition.agents[0].args[0].value == value


@pytest.mark.parametrize("value", [b"\xff\x00opaque", None])
def testAgentArgument_withBinaryValue_encodesOpaqueBytes(
    value: Optional[bytes],
) -> None:
    """The storage encoder supports binary arguments without text conversion."""
    assert models.AgentArgument.to_bytes("binary", value) == value


@pytest.mark.parametrize("value", [b"opaque", memoryview(b"opaque"), None])
def testCloudTransport_withOpaqueOrMissingValue_preservesValue(
    value: Optional[bytes | memoryview],
) -> None:
    """Cloud transport keeps bytes and memoryview values without text decoding."""
    assert cloud_runtime.CloudRuntime()._to_serialized(value) is value
