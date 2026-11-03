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


def testMessageFromData_whenAsnInfoProvided_roundTrips() -> None:
    data = {
        "asn": "15169",
        "website": "https://www.google.com",
        "network_type": "Content",
        "prefixes": [
            {
                "prefix": "8.8.8.0/24",
                "version": 4,
                "rpki_status": "valid",
                "country_code": "US",
            }
        ],
        "ip_count": 256,
        "neighbours": [{"asn": "3356", "type": "upstream"}],
        "rank": 10,
        "customer_cone": 800,
        "ixs": [{"name": "DE-CIX Frankfurt", "city": "Frankfurt", "speed": 100000}],
        "related_asns": ["36040"],
        "tags": ["cdn", "anycast"],
    }

    serialized = agent_message.Message.from_data("v3.asset.asn", data)
    deserialized = agent_message.Message.from_raw("v3.asset.asn", serialized.raw)

    assert deserialized.selector == "v3.asset.asn"
    assert deserialized.data == data
