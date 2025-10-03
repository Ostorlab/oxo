from src.ostorlab.agent.message.proto.v3.asset.domain_name.service import service_pb2


def testMessage_whenCreateWithValidData_shouldSerializeAndDeserializeCorrectly():
    message = service_pb2.Message()
    message.name = "HTTP"
    message.port = 80
    message.schema = "http"
    message.state = "open"
    
    serialized = message.SerializeToString()
    deserialized = service_pb2.Message()
    deserialized.ParseFromString(serialized)
    
    assert deserialized.name == "HTTP"
    assert deserialized.port == 80
    assert deserialized.schema == "http"
    assert deserialized.state == "open"


def testMessage_whenCreateEmpty_shouldHaveDefaultValues():
    message = service_pb2.Message()
    
    assert message.name == ""
    assert message.port == 0
    assert message.schema == ""
    assert message.state == ""


def testMessage_whenSerializeEmpty_shouldDeserializeToEmpty():
    message = service_pb2.Message()
    
    serialized = message.SerializeToString()
    deserialized = service_pb2.Message()
    deserialized.ParseFromString(serialized)
    
    assert deserialized.name == ""
    assert deserialized.port == 0
    assert deserialized.schema == ""
    assert deserialized.state == ""