from src.ostorlab.agent.message.proto.v3.asset.network import network_pb2


def testMessage_whenCreateWithCidr_shouldSerializeAndDeserializeCorrectly():
    message = network_pb2.Message()
    message.cidr = "45.237.228.0/22"

    serialized = message.SerializeToString()
    deserialized = network_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert deserialized.cidr == "45.237.228.0/22"


def testMessage_whenCreateWithIps_shouldSerializeAndDeserializeCorrectly():
    message = network_pb2.Message()
    ip = message.ips.add()
    ip.host = "45.237.228.0"
    ip.mask = "22"
    ip.version = 4

    serialized = message.SerializeToString()
    deserialized = network_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert len(deserialized.ips) == 1
    assert deserialized.ips[0].host == "45.237.228.0"
    assert deserialized.ips[0].mask == "22"
    assert deserialized.ips[0].version == 4


def testMessage_whenCreateEmpty_shouldHaveDefaultValues():
    message = network_pb2.Message()

    assert message.cidr == ""
    assert len(message.ips) == 0
