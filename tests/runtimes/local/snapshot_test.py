"""Unit tests for the universe snapshot used to pause and resume scans."""

import datetime
import gzip
from unittest import mock

import pytest
from docker import errors as docker_errors
from pytest_mock import plugin

from ostorlab.runtimes.local import snapshot
from ostorlab.runtimes.proto import universe_snapshot_pb2


def _service(
    mocker: plugin.MockerFixture,
    name: str,
    replicas: int,
    labels: dict[str, str] | None = None,
    restart_condition: str = "any",
) -> mock.MagicMock:
    service = mocker.MagicMock()
    service.name = name
    service.attrs = {
        "Spec": {
            "Mode": {"Replicated": {"Replicas": replicas}},
            "Labels": {"ostorlab.universe": "42"} | (labels or {}),
            "TaskTemplate": {"RestartPolicy": {"Condition": restart_condition}},
        }
    }
    return service


def _universe_snapshot() -> snapshot.Snapshot:
    return snapshot.Snapshot(
        universe_snapshot_pb2.UniverseSnapshot(
            version=snapshot.SNAPSHOT_VERSION,
            universe="42",
            paused_at_ms=1790000000000,
            exchanges=[
                universe_snapshot_pb2.Exchange(
                    name="ostorlab_topic_exchange", type="topic", durable=True
                )
            ],
            queues=[
                universe_snapshot_pb2.Queue(
                    name="nmap_queue",
                    durable=True,
                    arguments=universe_snapshot_pb2.FieldTable(
                        fields={
                            "x-max-priority": universe_snapshot_pb2.FieldValue(
                                int_value=255
                            )
                        }
                    ),
                    bindings=[
                        universe_snapshot_pb2.Binding(
                            exchange="ostorlab_topic_exchange",
                            routing_key="v3.asset.ip.#",
                        )
                    ],
                    messages=[
                        universe_snapshot_pb2.Message(
                            body=b"\x0a\x04\x08\x08\x08\x08",
                            routing_key="v3.asset.ip.v4.0f3c",
                            priority=1,
                            delivery_mode=2,
                        )
                    ],
                )
            ],
            redis_keys=[
                universe_snapshot_pb2.RedisKey(
                    key=b"agent_nmap_asset", ttl_ms=0, value=b"\x00\x05dump"
                )
            ],
        )
    )


def testSnapshot_whenSerialized_isRestoredIdenticallyAsRawBytes() -> None:
    original = _universe_snapshot()

    data = original.to_bytes()
    restored = snapshot.Snapshot.from_bytes(data)

    assert restored.proto == original.proto
    assert restored.messages_count == 1
    assert restored.universe == "42"
    assert restored.paused_at == datetime.datetime.fromtimestamp(
        1790000000, tz=datetime.timezone.utc
    )
    assert (
        universe_snapshot_pb2.UniverseSnapshot.FromString(gzip.decompress(data))
        .queues[0]
        .messages[0]
        .body
        == b"\x0a\x04\x08\x08\x08\x08"
    )


def testSnapshot_whenVersionIsUnknown_raisesInvalidSnapshot() -> None:
    data = gzip.compress(
        universe_snapshot_pb2.UniverseSnapshot(version=99).SerializeToString()
    )

    with pytest.raises(snapshot.InvalidSnapshotError):
        snapshot.Snapshot.from_bytes(data)


def testSnapshot_whenDataIsNotGzip_raisesInvalidSnapshot() -> None:
    with pytest.raises(snapshot.InvalidSnapshotError):
        snapshot.Snapshot.from_bytes(b"not a snapshot")


def testSnapshot_whenDataIsNotProtobuf_raisesInvalidSnapshot() -> None:
    with pytest.raises(snapshot.InvalidSnapshotError):
        snapshot.Snapshot.from_bytes(gzip.compress(b"\xff\xff\xff\xff"))


def testSnapshot_whenGzipBodyIsCorrupted_raisesInvalidSnapshot() -> None:
    data = bytearray(_universe_snapshot().to_bytes())
    # Keep the gzip header, corrupt the deflate stream right after it.
    data[10:20] = b"\xff" * 10

    with pytest.raises(snapshot.InvalidSnapshotError):
        snapshot.Snapshot.from_bytes(bytes(data))


def testStopUniverseAgents_whenAgentsRun_scalesThemToZeroAndKeepsTheirReplicas(
    mocker: plugin.MockerFixture,
) -> None:
    nmap = _service(mocker, "nmap_42", replicas=3)
    stop_scan = _service(mocker, "stop_scan_42", replicas=1)
    stopped_tracker = _service(mocker, "tracker_42", replicas=0)
    inject_asset = _service(
        mocker, "inject_asset_42", replicas=1, restart_condition="none"
    )
    docker_client = mocker.MagicMock()
    docker_client.services.list.return_value = [
        nmap,
        stop_scan,
        stopped_tracker,
        inject_asset,
    ]
    # nmap still running on the first check, then nmap, the stopped tracker and the asset injection all finished.
    docker_client.services.get.return_value.tasks.side_effect = [
        [{"Status": {"State": "running"}}],
        [{"Status": {"State": "shutdown"}}],
        [{"Status": {"State": "shutdown"}}],
        [{"Status": {"State": "complete"}}],
    ]
    mocker.patch("ostorlab.runtimes.local.snapshot.time.sleep")

    replicas = snapshot.stop_universe_agents(
        docker_client, universe="42", keep_services={"stop_scan_42"}
    )

    assert replicas == {"nmap_42": 3}
    update = nmap.update.call_args.kwargs
    assert update["mode"].replicas == 0
    assert update["labels"] == {
        "ostorlab.universe": "42",
        snapshot.REPLICAS_LABEL: "3",
    }
    stop_scan.update.assert_not_called()
    stopped_tracker.update.assert_not_called()
    inject_asset.update.assert_not_called()
    filters = docker_client.services.list.call_args.kwargs["filters"]
    assert filters == {"label": ["ostorlab.universe=42", "ostorlab.queue_name"]}


def testStopUniverseAgents_whenAgentWasStoppedByAnEarlierAttempt_keepsItsOriginalReplicas(
    mocker: plugin.MockerFixture,
) -> None:
    nmap = _service(
        mocker, "nmap_42", replicas=0, labels={snapshot.REPLICAS_LABEL: "3"}
    )
    docker_client = mocker.MagicMock()
    docker_client.services.list.return_value = [nmap]
    docker_client.services.get.return_value.tasks.return_value = []

    replicas = snapshot.stop_universe_agents(docker_client, universe="42")

    assert replicas == {"nmap_42": 3}
    nmap.update.assert_not_called()


def testStopUniverseAgents_whenAgentStoppedEarlierWasStartedAgain_scalesItDownKeepingItsReplicas(
    mocker: plugin.MockerFixture,
) -> None:
    nmap = _service(
        mocker, "nmap_42", replicas=2, labels={snapshot.REPLICAS_LABEL: "3"}
    )
    docker_client = mocker.MagicMock()
    docker_client.services.list.return_value = [nmap]
    docker_client.services.get.return_value.tasks.return_value = []

    replicas = snapshot.stop_universe_agents(docker_client, universe="42")

    assert replicas == {"nmap_42": 3}
    assert nmap.update.call_args.kwargs["mode"].replicas == 0
    assert nmap.update.call_args.kwargs["labels"][snapshot.REPLICAS_LABEL] == "3"


def testStopUniverseAgents_whenServiceIsRemovedWhileWaiting_treatsItAsStopped(
    mocker: plugin.MockerFixture,
) -> None:
    inject_asset = _service(
        mocker, "inject_asset_42", replicas=1, restart_condition="none"
    )
    docker_client = mocker.MagicMock()
    docker_client.services.list.return_value = [inject_asset]
    docker_client.services.get.side_effect = docker_errors.NotFound("removed")

    replicas = snapshot.stop_universe_agents(docker_client, universe="42")

    assert replicas == {}


def testStopUniverseAgents_whenAgentsKeepRunning_raisesAgentsNotStopped(
    mocker: plugin.MockerFixture,
) -> None:
    nmap = _service(mocker, "nmap_42", 1)
    docker_client = mocker.MagicMock()
    docker_client.services.list.return_value = [nmap]
    docker_client.services.get.return_value.tasks.return_value = [
        {"Status": {"State": "running"}}
    ]
    mocker.patch("ostorlab.runtimes.local.snapshot.time.sleep")

    with pytest.raises(snapshot.AgentsNotStoppedError):
        snapshot.stop_universe_agents(
            docker_client, universe="42", timeout=datetime.timedelta(seconds=0)
        )

    # The replicas stay on the service, the rollback starts it again.
    assert nmap.update.call_args.kwargs["labels"][snapshot.REPLICAS_LABEL] == "1"


@pytest.mark.parametrize("state", ["pending", "assigned", "preparing", "ready"])
def testStopUniverseAgents_whenATaskIsStillStarting_raisesAgentsNotStopped(
    mocker: plugin.MockerFixture, state: str
) -> None:
    """A task not yet running can still start and consume messages while the snapshot is taken."""
    nmap = _service(mocker, "nmap_42", 1)
    docker_client = mocker.MagicMock()
    docker_client.services.list.return_value = [nmap]
    docker_client.services.get.return_value.tasks.return_value = [
        {"Status": {"State": "shutdown"}},
        {"Status": {"State": state}},
    ]
    mocker.patch("ostorlab.runtimes.local.snapshot.time.sleep")

    with pytest.raises(snapshot.AgentsNotStoppedError):
        snapshot.stop_universe_agents(
            docker_client, universe="42", timeout=datetime.timedelta(seconds=0)
        )


def testStopUniverseAgents_whenRunOnceServiceStillRuns_waitsForItWithoutScalingIt(
    mocker: plugin.MockerFixture,
) -> None:
    """An asset injection still publishing would add messages after the queues are read, they would be lost."""
    inject_asset = _service(
        mocker, "inject_asset_42", replicas=1, restart_condition="none"
    )
    docker_client = mocker.MagicMock()
    docker_client.services.list.return_value = [inject_asset]
    docker_client.services.get.return_value.tasks.return_value = [
        {"Status": {"State": "running"}}
    ]
    mocker.patch("ostorlab.runtimes.local.snapshot.time.sleep")

    with pytest.raises(snapshot.AgentsNotStoppedError):
        snapshot.stop_universe_agents(
            docker_client, universe="42", timeout=datetime.timedelta(seconds=0)
        )

    inject_asset.update.assert_not_called()
    docker_client.services.get.assert_called_with("inject_asset_42")


def testStartUniverseAgents_always_scalesStoppedServicesBackAndRemovesTheirLabel(
    mocker: plugin.MockerFixture,
) -> None:
    nmap = _service(
        mocker, "nmap_42", replicas=0, labels={snapshot.REPLICAS_LABEL: "3"}
    )
    xss = _service(mocker, "xss_42", replicas=2)
    docker_client = mocker.MagicMock()
    docker_client.services.list.return_value = [nmap, xss]

    snapshot.start_universe_agents(docker_client, universe="42")

    update = nmap.update.call_args.kwargs
    assert update["mode"].replicas == 3
    assert update["labels"] == {"ostorlab.universe": "42"}
    xss.update.assert_not_called()
