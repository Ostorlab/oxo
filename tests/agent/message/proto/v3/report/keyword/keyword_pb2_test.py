from ostorlab.agent.message.proto.v3.report.keyword import keyword_pb2


def testMessage_whenCreateWithValidData_shouldSerializeAndDeserializeCorrectly() -> (
    None
):
    msg = keyword_pb2.Message()
    msg.keyword = "test-keyword"

    serialized = msg.SerializeToString()
    deserialized_msg = keyword_pb2.Message()
    deserialized_msg.ParseFromString(serialized)

    assert deserialized_msg.keyword == "test-keyword"


def testMessage_whenCreateEmpty_shouldHaveDefaultValues() -> None:
    msg = keyword_pb2.Message()

    assert msg.keyword == ""
