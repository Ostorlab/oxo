"""State of a local scan kept on disk, so a scan paused by `oxo scan pause` can be resumed by another oxo process.

Each scan has a directory under `SCANS_DIRECTORY`, named after its id:

- `definition.json`: the agents and the tracker settings of the scan, written when it starts. The process pausing the
  scan is not the one that started it, the definition is read back when the scan resumes.
- `snapshot.json.gz`: the MQ and Redis state of the scan, written when it is paused, see `snapshot.save_file`.
"""

from __future__ import annotations

import base64
import dataclasses
import json
import pathlib
import shutil
import typing

from ostorlab import configuration_manager
from ostorlab import exceptions
from ostorlab.runtimes import definitions
from ostorlab.utils import definitions as utils_definitions

SCANS_DIRECTORY = configuration_manager.OSTORLAB_PRIVATE_DIR / "scans"
DEFINITION_FILE = "definition.json"
SNAPSHOT_FILE = "snapshot.json.gz"


class Error(exceptions.OstorlabError):
    """Base error of the local scan state."""


class InvalidDefinitionError(Error):
    """The stored definition of the scan cannot be read."""


@dataclasses.dataclass(frozen=True)
class ScanDefinition:
    """What the local runtime needs to start the agents of a scan again."""

    agent_group_definition: definitions.AgentGroupDefinition
    has_tracker: bool
    timeout: int | None
    init_sleep: int | None
    follow: list[str]


def directory(scan_id: int | str) -> pathlib.Path:
    """Directory of the state of a scan."""
    return SCANS_DIRECTORY / str(scan_id)


def snapshot_path(scan_id: int | str) -> pathlib.Path:
    """Path of the snapshot of a paused scan."""
    return directory(scan_id) / SNAPSHOT_FILE


def save_definition(scan_id: int | str, scan_definition: ScanDefinition) -> None:
    """Store the definition of a scan, replacing the previous one.

    Raises:
        Error: When the definition cannot be serialized or written.
    """
    try:
        content = json.dumps(
            {
                "agents": [
                    _agent_to_dict(agent)
                    for agent in scan_definition.agent_group_definition.agents
                ],
                "has_tracker": scan_definition.has_tracker,
                "timeout": scan_definition.timeout,
                "init_sleep": scan_definition.init_sleep,
                "follow": scan_definition.follow,
            }
        )
    # An argument value JSON cannot represent, like bytes nested in a list, raises `TypeError` or `ValueError`.
    except (TypeError, ValueError) as e:
        raise Error(f"could not serialize the definition of scan {scan_id}: {e}") from e
    path = directory(scan_id) / DEFINITION_FILE
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    except OSError as e:
        raise Error(f"could not write the definition of scan {scan_id}: {e}") from e


def load_definition(scan_id: int | str) -> ScanDefinition | None:
    """Read the definition of a scan.

    Returns:
        The definition, None when the scan has none, like a scan started before oxo stored them.

    Raises:
        Error: When the file cannot be read.
        InvalidDefinitionError: When the file is not a scan definition.
    """
    path = directory(scan_id) / DEFINITION_FILE
    try:
        content = path.read_text()
    except FileNotFoundError:
        return None
    except OSError as e:
        raise Error(f"could not read the definition of scan {scan_id}: {e}") from e
    try:
        document = json.loads(content)
        return ScanDefinition(
            agent_group_definition=definitions.AgentGroupDefinition(
                agents=[_agent_from_dict(agent) for agent in document["agents"]]
            ),
            has_tracker=bool(document["has_tracker"]),
            timeout=document["timeout"],
            init_sleep=document["init_sleep"],
            follow=list(document["follow"]),
        )
    except (ValueError, KeyError, TypeError) as e:
        raise InvalidDefinitionError(
            f"invalid definition of scan {scan_id}: {e}"
        ) from e


def delete_snapshot(scan_id: int | str) -> None:
    """Remove the snapshot of a scan once it resumed, a snapshot is restored once."""
    snapshot_path(scan_id).unlink(missing_ok=True)


def delete(scan_id: int | str) -> None:
    """Remove the whole state of a scan, once it is stopped it cannot be resumed."""
    shutil.rmtree(directory(scan_id), ignore_errors=True)


def _agent_to_dict(agent: definitions.AgentSettings) -> dict[str, typing.Any]:
    """The settings of an agent set by its definition, the bus, Redis and snapshot settings are set by the runtime
    when it starts the agent."""
    return {
        "key": agent.key,
        "version": agent.version,
        "args": [_arg_to_dict(arg) for arg in agent.args],
        "constraints": _optional_list(agent.constraints),
        "mounts": _optional_list(agent.mounts),
        "restart_policy": agent.restart_policy,
        "mem_limit": agent.mem_limit,
        "open_ports": [
            {
                "source_port": port.source_port,
                "destination_port": port.destination_port,
            }
            for port in agent.open_ports
        ],
        "replicas": agent.replicas,
        "healthcheck_host": agent.healthcheck_host,
        "healthcheck_port": agent.healthcheck_port,
        "caps": _optional_list(agent.caps),
        "cyclic_processing_limit": agent.cyclic_processing_limit,
        "depth_processing_limit": agent.depth_processing_limit,
        "accepted_agents": _optional_list(agent.accepted_agents),
        "in_selectors": _optional_list(agent.in_selectors),
        "service_name": agent.service_name,
    }


def _agent_from_dict(agent: dict[str, typing.Any]) -> definitions.AgentSettings:
    return definitions.AgentSettings(
        key=agent["key"],
        version=agent["version"],
        args=[_arg_from_dict(arg) for arg in agent["args"]],
        constraints=agent["constraints"],
        mounts=agent["mounts"],
        restart_policy=agent["restart_policy"],
        mem_limit=agent["mem_limit"],
        open_ports=[
            utils_definitions.PortMapping(
                source_port=port["source_port"],
                destination_port=port["destination_port"],
            )
            for port in agent["open_ports"]
        ],
        replicas=agent["replicas"],
        healthcheck_host=agent["healthcheck_host"],
        healthcheck_port=agent["healthcheck_port"],
        caps=agent["caps"],
        cyclic_processing_limit=agent["cyclic_processing_limit"],
        depth_processing_limit=agent["depth_processing_limit"],
        accepted_agents=agent["accepted_agents"],
        in_selectors=agent["in_selectors"],
        service_name=agent["service_name"],
    )


def _arg_to_dict(arg: utils_definitions.Arg) -> dict[str, typing.Any]:
    # A binary value is not JSON serializable, it is stored in base64.
    if isinstance(arg.value, bytes):
        return {
            "name": arg.name,
            "type": arg.type,
            "value": base64.b64encode(arg.value).decode(),
            "is_bytes": True,
        }
    return {"name": arg.name, "type": arg.type, "value": arg.value, "is_bytes": False}


def _arg_from_dict(arg: dict[str, typing.Any]) -> utils_definitions.Arg:
    value = arg["value"]
    if arg["is_bytes"] is True:
        value = base64.b64decode(value, validate=True)
    return utils_definitions.Arg(name=arg["name"], type=arg["type"], value=value)


def _optional_list(
    values: typing.Sequence[str] | None,
) -> list[str] | None:
    return list(values) if values is not None else None
