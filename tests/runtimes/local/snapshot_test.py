"""Unit tests for the universe snapshot used to pause and resume scans."""

import asyncio
import datetime
import gzip

import pytest
from pytest_httpx import HTTPXMock
from pytest_mock import plugin

from ostorlab.runtimes.local import snapshot
from ostorlab.runtimes.local.proto import universe_snapshot_pb2


def _service(
    mocker: plugin.MockerFixture,
    name: str,
    replicas: int,
    labels: dict[str, str] | None = None,
    restart_condition: str = "any",
):
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
                    arguments=snapshot._to_field_table({"x-max-priority": 255}),
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


def testFieldTable_whenConvertedBackAndForth_keepsAmqpValues() -> None:
    headers = {
        "raw": bytearray(b"\x00\x01"),
        "count": 3,
        "ratio": 0.5,
        "enabled": True,
        "nested": {"values": [bytearray(b"\x02"), 1, "text"]},
    }

    table = universe_snapshot_pb2.FieldTable.FromString(
        snapshot._to_field_table(headers | {"absent": None}).SerializeToString()
    )

    assert snapshot._from_field_table(table) == headers
    assert isinstance(snapshot._from_field_table(table)["enabled"], bool)


def testBuildMessage_whenRestoringSerializedMessage_keepsBodyRoutingKeyAndProperties(
    mocker: plugin.MockerFixture,
) -> None:
    incoming = mocker.MagicMock(
        body=b"\x0a\x02body",
        exchange="ostorlab_topic_exchange",
        routing_key="v3.asset.domain_name.1a2b",
        priority=4,
        delivery_mode=2,
        content_type=None,
        content_encoding=None,
        correlation_id=None,
        message_id="m-1",
        type=None,
        app_id=None,
        reply_to="nmap_replies",
        expiration=30.0,
        timestamp=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
        headers={"trace": bytearray(b"\x01")},
    )

    serialized = snapshot._serialize_message(incoming)
    rebuilt = snapshot._build_message(serialized, queue_name="nmap_queue")

    assert serialized.routing_key == "v3.asset.domain_name.1a2b"
    assert serialized.HasField("content_type") is False
    assert rebuilt.body == b"\x0a\x02body"
    assert rebuilt.priority == 4
    assert rebuilt.message_id == "m-1"
    assert rebuilt.reply_to == "nmap_replies"
    assert rebuilt.expiration == 30.0
    assert rebuilt.timestamp == datetime.datetime(
        2026, 1, 1, tzinfo=datetime.timezone.utc
    )
    assert rebuilt.headers == {
        "trace": bytearray(b"\x01"),
        snapshot.RESTORE_QUEUE_HEADER: "nmap_queue",
    }


def testRestoreRedis_always_restoresRawKeysOnly(
    mocker: plugin.MockerFixture,
) -> None:
    redis_client = mocker.MagicMock()
    mocker.patch(
        "redis.Redis.from_url"
    ).return_value.__enter__.return_value = redis_client

    snapshot._restore_redis("redis://redis_42:6379/", _universe_snapshot())

    redis_client.pipeline.return_value.restore.assert_called_once_with(
        b"agent_nmap_asset", 0, b"\x00\x05dump", replace=True
    )
    redis_client.set.assert_not_called()
    redis_client.incrbyfloat.assert_not_called()


def testDumpRedis_whenKeysDescribeTheCurrentRun_leavesThemOut(
    mocker: plugin.MockerFixture,
) -> None:
    """A resumed universe starts a new run, the tracker clock for example starts again from zero."""
    redis_client = mocker.MagicMock()
    mocker.patch(
        "redis.Redis.from_url"
    ).return_value.__enter__.return_value = redis_client
    redis_client.scan_iter.return_value = [
        b"agent_nmap_asset",
        b"ostorlab:run:scan_start_datetime",
    ]
    redis_client.dump.return_value = b"\x00\x05dump"
    redis_client.pttl.return_value = -1

    keys = snapshot._dump_redis("redis://redis_42:6379/")

    assert [key.key for key in keys] == [b"agent_nmap_asset"]
    redis_client.dump.assert_called_once_with(b"agent_nmap_asset")


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


def testListMqTopology_whenQueueIsBoundToAmqExchange_skipsThatBinding(
    httpx_mock: HTTPXMock,
) -> None:
    """amq.* exchanges are not captured, their bindings would reference an exchange missing on restore."""
    management_url = "http://guest:guest@mq_42:15672/"
    httpx_mock.add_response(
        url=f"{management_url}api/exchanges/%2F",
        json=[
            {"name": "", "type": "direct", "durable": True, "auto_delete": False},
            {
                "name": "amq.direct",
                "type": "direct",
                "durable": True,
                "auto_delete": False,
            },
            {
                "name": "ostorlab_topic",
                "type": "topic",
                "durable": True,
                "auto_delete": False,
            },
        ],
    )
    httpx_mock.add_response(
        url=f"{management_url}api/queues/%2F",
        json=[
            {
                "name": "nmap_queue",
                "durable": True,
                "arguments": {"x-max-priority": 255},
            }
        ],
    )
    httpx_mock.add_response(
        url=f"{management_url}api/queues/%2F/nmap_queue/bindings",
        json=[
            {"source": "", "routing_key": "nmap_queue"},
            {"source": "amq.direct", "routing_key": "nmap"},
            {"source": "ostorlab_topic", "routing_key": "v3.asset.ip.#"},
        ],
    )

    exchanges, queues = snapshot._list_mq_topology(management_url, "/")

    assert [exchange.name for exchange in exchanges] == ["ostorlab_topic"]
    assert [binding.exchange for binding in queues[0].bindings] == ["ostorlab_topic"]


def testRestoreMq_always_routesEachMessageToItsQueueAndRemovesTheRestoreExchange(
    mocker: plugin.MockerFixture,
) -> None:
    """Messages are published through a temporary headers exchange, keeping their original routing key."""
    connection = mocker.AsyncMock()
    mocker.patch("aio_pika.connect", return_value=connection)
    channel = connection.channel.return_value
    topic_exchange = mocker.AsyncMock()
    restore_exchange = mocker.AsyncMock()
    channel.declare_exchange.side_effect = [topic_exchange, restore_exchange]
    queue = channel.declare_queue.return_value

    asyncio.run(snapshot._restore_mq("amqp://mq_42", _universe_snapshot()))

    assert (
        channel.declare_exchange.call_args_list[0].args[0] == "ostorlab_topic_exchange"
    )
    assert (
        channel.declare_exchange.call_args_list[1].args[0] == snapshot.RESTORE_EXCHANGE
    )
    assert channel.declare_queue.call_args.args[0] == "nmap_queue"
    queue.bind.assert_any_call(
        topic_exchange, routing_key="v3.asset.ip.#", arguments={}
    )
    restore_binding = {"x-match": "all", snapshot.RESTORE_QUEUE_HEADER: "nmap_queue"}
    queue.bind.assert_any_call(restore_exchange, arguments=restore_binding)
    published = restore_exchange.publish.call_args
    assert published.kwargs["routing_key"] == "v3.asset.ip.v4.0f3c"
    assert published.args[0].headers[snapshot.RESTORE_QUEUE_HEADER] == "nmap_queue"
    queue.unbind.assert_called_once_with(restore_exchange, arguments=restore_binding)
    restore_exchange.delete.assert_called_once()
    connection.close.assert_called_once()
