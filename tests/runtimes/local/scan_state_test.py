"""Unit tests for the state of the local scans kept on disk."""

import pathlib

import pytest
from ostorlab.runtimes import definitions
from ostorlab.runtimes.local import scan_state
from ostorlab.utils import definitions as utils_definitions

SCAN_DEFINITION = scan_state.ScanDefinition(
    agent_group_definition=definitions.AgentGroupDefinition(
        agents=[
            definitions.AgentSettings(
                key="agent/ostorlab/nmap",
                version="1.2.0",
                args=[
                    utils_definitions.Arg(name="ports", type="array", value=[80, 443]),
                    utils_definitions.Arg(name="key", type="binary", value=b"\x00\xff"),
                ],
                constraints=["node.role==manager"],
                mounts=["/tmp:/tmp"],
                restart_policy="any",
                mem_limit=1024,
                open_ports=[
                    utils_definitions.PortMapping(source_port=8080, destination_port=80)
                ],
                replicas=2,
                caps=["NET_ADMIN"],
                cyclic_processing_limit=3,
                depth_processing_limit=4,
                accepted_agents=["agent/ostorlab/inject_asset"],
                in_selectors=["v3.asset.ip"],
                service_name="nmap_scanner",
            ),
            definitions.AgentSettings(key="agent/ostorlab/tsunami"),
        ]
    ),
    has_tracker=True,
    timeout=600,
    init_sleep=10,
    follow=["agent/ostorlab/nmap"],
)


def testSaveDefinitionThenLoadDefinition_always_returnsTheSavedDefinition() -> None:
    """The agents and the tracker settings load back identical, binary arguments and versions included."""
    scan_state.save_definition(7, SCAN_DEFINITION)

    assert scan_state.load_definition(7) == SCAN_DEFINITION


def testSaveDefinition_always_leavesOutTheSettingsSetByTheRuntime() -> None:
    """The bus, Redis and snapshot settings of a started agent are not kept, the runtime sets new ones on resume."""
    agent = definitions.AgentSettings(
        key="agent/ostorlab/nmap",
        bus_url="amqp://guest:guest@mq_7:5672/",
        redis_url="redis://redis_7:6379/",
    )
    scan_definition = scan_state.ScanDefinition(
        agent_group_definition=definitions.AgentGroupDefinition(agents=[agent]),
        has_tracker=False,
        timeout=None,
        init_sleep=None,
        follow=[],
    )

    scan_state.save_definition(7, scan_definition)
    loaded = scan_state.load_definition(7)

    assert loaded is not None
    loaded_agent = loaded.agent_group_definition.agents[0]
    assert loaded_agent.bus_url == ""
    assert loaded_agent.redis_url is None


def testLoadDefinition_whenScanHasNoDefinition_returnsNone() -> None:
    """A scan started before the definitions were kept has none."""
    assert scan_state.load_definition(7) is None


def testLoadDefinition_whenFileIsNotADefinition_raisesInvalidDefinitionError(
    scans_directory: pathlib.Path,
) -> None:
    """A corrupted definition is reported, the scan is not resumed with other agents."""
    (scans_directory / "7").mkdir(parents=True)
    (scans_directory / "7" / scan_state.DEFINITION_FILE).write_text('{"agents": 1}')

    with pytest.raises(scan_state.InvalidDefinitionError):
        scan_state.load_definition(7)


def testDeleteSnapshot_always_keepsTheDefinition(
    scans_directory: pathlib.Path,
) -> None:
    """A resumed scan keeps its definition to be paused again."""
    scan_state.save_definition(7, SCAN_DEFINITION)
    scan_state.snapshot_path(7).write_bytes(b"snapshot")

    scan_state.delete_snapshot(7)

    assert scan_state.snapshot_path(7).exists() is False
    assert scan_state.load_definition(7) == SCAN_DEFINITION


def testDelete_always_removesTheStateOfTheScan(scans_directory: pathlib.Path) -> None:
    """A stopped scan cannot be resumed, its state is removed."""
    scan_state.save_definition(7, SCAN_DEFINITION)
    scan_state.snapshot_path(7).write_bytes(b"snapshot")

    scan_state.delete(7)

    assert (scans_directory / "7").exists() is False


def testDelete_whenScanHasNoState_doesNotRaise() -> None:
    """Stopping a scan without state does nothing."""
    scan_state.delete(7)
