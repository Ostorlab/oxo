from ostorlab.agent.message.proto.v3.asset.file.api_schema.wsdl import wsdl_pb2


def testMessage_whenCreateWithValidData_shouldSerializeAndDeserializeCorrectly():
    message = wsdl_pb2.Message()
    message.content = b'<?xml version="1.0" encoding="UTF-8"?><definitions xmlns="http://schemas.xmlsoap.org/wsdl/"></definitions>'
    message.path = "/wsdl/service.wsdl"
    message.schema_type = "wsdl"
    
    serialized = message.SerializeToString()
    deserialized = wsdl_pb2.Message()
    deserialized.ParseFromString(serialized)
    
    assert deserialized.content == b'<?xml version="1.0" encoding="UTF-8"?><definitions xmlns="http://schemas.xmlsoap.org/wsdl/"></definitions>'
    assert deserialized.path == "/wsdl/service.wsdl"
    assert deserialized.schema_type == "wsdl"


def testMessage_whenCreateEmpty_shouldHaveDefaultValues():
    message = wsdl_pb2.Message()
    
    assert message.content == b""
    assert message.path == ""
    assert message.schema_type == "wsdl"


def testMessage_whenSerializeEmpty_shouldDeserializeToEmpty():
    message = wsdl_pb2.Message()
    
    serialized = message.SerializeToString()
    deserialized = wsdl_pb2.Message()
    deserialized.ParseFromString(serialized)
    
    assert deserialized.content == b""
    assert deserialized.path == ""
    assert deserialized.schema_type == "wsdl"