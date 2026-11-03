from ostorlab.agent.message import message as agent_message


def testMessageFromData_whenAsnProvided_roundTrips() -> None:
    serialized = agent_message.Message.from_data(
        "v3.asset.asn",
        {"asn": "AS268302"},
    )

    deserialized = agent_message.Message.from_raw("v3.asset.asn", serialized.raw)

    assert deserialized.selector == "v3.asset.asn"
    assert deserialized.data == {"asn": "AS268302"}


def testMessageFromData_whenAsnHasNoPrefix_roundTrips() -> None:
    serialized = agent_message.Message.from_data(
        "v3.asset.asn",
        {"asn": "268302"},
    )

    deserialized = agent_message.Message.from_raw("v3.asset.asn", serialized.raw)

    assert deserialized.selector == "v3.asset.asn"
    assert deserialized.data == {"asn": "268302"}
