from src.ostorlab.agent.message.proto.v3.asset.asn import asn_pb2


def testMessage_whenCreateWithAsn_shouldSerializeAndDeserializeCorrectly():
    message = asn_pb2.Message()
    message.asn = "AS268302"

    serialized = message.SerializeToString()
    deserialized = asn_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert deserialized.asn == "AS268302"


def testMessage_whenCreateEmpty_shouldHaveDefaultValues():
    message = asn_pb2.Message()

    assert message.asn == ""


def testMessage_whenSerializeEmpty_shouldDeserializeToEmpty():
    message = asn_pb2.Message()

    serialized = message.SerializeToString()
    deserialized = asn_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert deserialized.asn == ""
