from ostorlab.agent.message import message as agent_message


def testMessageFromData_whenAsnCidrProvided_roundTrips() -> None:
    data = {
        "host": "8.8.8.8",
        "version": 4,
        "asn_number": 15169,
        "asn_cidr": "8.8.8.0/24",
    }

    serialized = agent_message.Message.from_data("v3.asset.ip.v4.whois", data)
    deserialized = agent_message.Message.from_raw(
        "v3.asset.ip.v4.whois", serialized.raw
    )

    assert deserialized.data["asn_cidr"] == "8.8.8.0/24"
