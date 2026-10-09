from ostorlab.runtimes.proto import universe_snapshot_pb2


def testUniverseSnapshot_whenSerialized_shouldDeserializeIdentically():
    universe_snapshot = universe_snapshot_pb2.UniverseSnapshot(
        version=1, universe="42", paused_at_ms=1790000000000
    )
    universe_snapshot.exchanges.add(name="ostorlab_topic_exchange", type="topic")
    queue = universe_snapshot.queues.add(name="nmap_queue", durable=True)
    queue.arguments.fields["x-max-priority"].int_value = 10
    queue.bindings.add(exchange="ostorlab_topic_exchange", routing_key="v3.#")
    message = queue.messages.add(
        body=b"\x00\xff", routing_key="v3.asset.ip.v4", priority=5, expiration=0.5
    )
    message.headers.fields["trace"].array_value.values.add(bytes_value=b"\x01")
    universe_snapshot.redis_keys.add(key=b"agent:key", ttl_ms=1000, value=b"\x09")

    deserialized = universe_snapshot_pb2.UniverseSnapshot.FromString(
        universe_snapshot.SerializeToString()
    )

    assert deserialized == universe_snapshot
    restored_message = deserialized.queues[0].messages[0]
    assert restored_message.body == b"\x00\xff"
    assert restored_message.expiration == 0.5
    assert (
        restored_message.headers.fields["trace"].array_value.values[0].bytes_value
        == b"\x01"
    )
    assert deserialized.redis_keys[0].value == b"\x09"


def testMessage_whenFieldIsNotSet_shouldReportItAsMissing():
    """The restore only sets the message properties the snapshot holds, proto2 tells them apart from defaults."""
    message = universe_snapshot_pb2.Message(body=b"", priority=0)

    deserialized = universe_snapshot_pb2.Message.FromString(message.SerializeToString())

    assert deserialized.HasField("priority") is True
    assert deserialized.HasField("expiration") is False
    assert deserialized.HasField("timestamp") is False
