from src.ostorlab.agent.message.proto.v3.asset.tracker_id import tracker_id_pb2


def testMessage_whenCreateWithValidData_shouldSerializeAndDeserializeCorrectly():
    message = tracker_id_pb2.Message()
    message.id = "a1b2c3"
    message.source = "reverse_search"

    serialized = message.SerializeToString()
    deserialized = tracker_id_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert deserialized.id == "a1b2c3"
    assert deserialized.source == "reverse_search"


def testMessage_whenCreateEmpty_shouldHaveDefaultValues():
    message = tracker_id_pb2.Message()

    assert message.id == ""
    assert message.source == ""


def testMessage_whenSerializeEmpty_shouldDeserializeToEmpty():
    message = tracker_id_pb2.Message()

    serialized = message.SerializeToString()
    deserialized = tracker_id_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert deserialized.id == ""
    assert deserialized.source == ""
