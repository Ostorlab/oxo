from src.ostorlab.agent.message.proto.v3.asset.domain_name.whois import whois_pb2


def testMessage_whenCreateWithValidData_shouldSerializeAndDeserializeCorrectly():
    message = whois_pb2.Message()
    message.name = "example.com"
    message.registrar = "Example Registrar"
    message.whois_server = "whois.example.com"

    serialized = message.SerializeToString()
    deserialized = whois_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert deserialized.name == "example.com"
    assert deserialized.registrar == "Example Registrar"
    assert deserialized.whois_server == "whois.example.com"


def testMessage_whenCreateEmpty_shouldHaveDefaultValues():
    message = whois_pb2.Message()

    assert message.name == ""
    assert message.registrar == ""
    assert message.whois_server == ""


def testMessage_whenSerializeEmpty_shouldDeserializeToEmpty():
    message = whois_pb2.Message()

    serialized = message.SerializeToString()
    deserialized = whois_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert deserialized.name == ""
    assert deserialized.registrar == ""
    assert deserialized.whois_server == ""
