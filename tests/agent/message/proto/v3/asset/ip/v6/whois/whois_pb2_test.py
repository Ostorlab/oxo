from ostorlab.agent.message import message as agent_message


def testMessageFromData_whenIpv6AsnCidrProvided_roundTrips() -> None:
    data = {
        "host": "2001:4860:4860::8888",
        "version": 6,
        "asn_cidr": "2001:4860::/32",
    }

    serialized = agent_message.Message.from_data("v3.asset.ip.v6.whois", data)
    deserialized = agent_message.Message.from_raw(
        "v3.asset.ip.v6.whois", serialized.raw
    )

    assert deserialized.data["asn_cidr"] == "2001:4860::/32"
