from ostorlab.agent.message import message as agent_message


def testMessageFromData_whenOriginsProvided_roundTrips() -> None:
    data = {
        "host": "8.8.8.8",
        "version": 4,
        "prefix": "8.8.8.0/24",
        "origins": [{"asn": "15169", "rpki_status": "valid"}],
    }

    serialized = agent_message.Message.from_data("v3.asset.ip.v4.routing", data)
    deserialized = agent_message.Message.from_raw(
        "v3.asset.ip.v4.routing", serialized.raw
    )

    assert deserialized.data == data


def testMessageFromData_whenIpv6NotAnnounced_roundTrips() -> None:
    data = {"host": "2001:db8::1", "version": 6}

    serialized = agent_message.Message.from_data("v3.asset.ip.v6.routing", data)
    deserialized = agent_message.Message.from_raw(
        "v3.asset.ip.v6.routing", serialized.raw
    )

    assert deserialized.data == data
