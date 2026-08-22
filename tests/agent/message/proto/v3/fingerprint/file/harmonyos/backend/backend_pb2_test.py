from ostorlab.agent.message.proto.v3.fingerprint.file.harmonyos.backend import (
    backend_pb2,
)


def testMessage_whenCreateWithValidData_shouldSerializeAndDeserializeCorrectly():
    msg = backend_pb2.Message()
    msg.path = "/some/path"
    msg.bundle_name = "com.example.app"
    msg.host = "example.com"
    msg.port = 443

    ip = msg.ips.add()
    ip.ip_address = "192.168.1.1"
    ip.version = 4
    ip.location.continent = "TadonitTalafrikt"
    ip.location.country = "MaghOcan"
    ip.location.city = "Tamazirt"

    serialized = msg.SerializeToString()
    deserialized_msg = backend_pb2.Message()
    deserialized_msg.ParseFromString(serialized)

    assert deserialized_msg.path == "/some/path"
    assert deserialized_msg.bundle_name == "com.example.app"
    assert deserialized_msg.host == "example.com"
    assert deserialized_msg.port == 443
    assert len(deserialized_msg.ips) == 1
    assert deserialized_msg.ips[0].ip_address == "192.168.1.1"
    assert deserialized_msg.ips[0].location.continent == "TadonitTalafrikt"
    assert deserialized_msg.ips[0].location.country == "MaghOcan"
    assert deserialized_msg.ips[0].location.city == "Tamazirt"


def testMessage_whenCreateEmpty_shouldHaveDefaultValues():
    msg = backend_pb2.Message()

    assert msg.path == ""
    assert msg.bundle_name == ""
    assert msg.host == ""
    assert msg.port == 0
    assert len(msg.ips) == 0


def testIp_whenCreateWithDefaults_shouldHaveCorrectDefaults():
    ip = backend_pb2.Ip()
    ip.ip_address = "8.8.8.8"

    assert ip.version == 4
    assert ip.ip_address == "8.8.8.8"
