from ostorlab.agent.message import message as agent_message


def testMessageFromData_whenAsnWhoisProvided_roundTrips() -> None:
    data = {
        "asn": "15169",
        "name": "GOOGLE",
        "organisation": "Google LLC",
        "country": "US",
        "registry": "arin",
        "allocated": "2000-03-30",
        "updated": "2012-02-24",
        "rdap_url": "https://rdap.arin.net/registry/autnum/15169",
    }

    serialized = agent_message.Message.from_data("v3.asset.asn.whois", data)
    deserialized = agent_message.Message.from_raw("v3.asset.asn.whois", serialized.raw)

    assert deserialized.selector == "v3.asset.asn.whois"
    assert deserialized.data == data


def testMessageFromData_whenOnlyAsnProvided_roundTrips() -> None:
    serialized = agent_message.Message.from_data("v3.asset.asn.whois", {"asn": "15169"})

    deserialized = agent_message.Message.from_raw("v3.asset.asn.whois", serialized.raw)

    assert deserialized.data == {"asn": "15169"}
