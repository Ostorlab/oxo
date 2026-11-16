from ostorlab.agent.message import message as agent_message


def testMessageFromData_whenAsnFingerprintProvided_roundTrips() -> None:
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
        "traceroute": {
            "target": "8.8.8.1",
            "hops": [
                {"ip": "81.192.32.62", "asn": "6713", "rtt": 3.77},
                {},
                {"ip": "192.178.105.209", "asn": "15169", "rtt": 26.44},
            ],
        },
        "hosted_domains": [
            {"name": "dns.google", "ip": "8.8.8.8"},
            {"name": "www.google.com", "ip": "142.250.74.4"},
        ],
        "hosted_domains_count": 482,
    }

    serialized = agent_message.Message.from_data("v3.fingerprint.asn", data)
    deserialized = agent_message.Message.from_raw("v3.fingerprint.asn", serialized.raw)

    assert deserialized.selector == "v3.fingerprint.asn"
    assert deserialized.data == data


def testMessageFromData_whenOnlyAsnProvided_roundTrips() -> None:
    serialized = agent_message.Message.from_data("v3.fingerprint.asn", {"asn": "15169"})

    deserialized = agent_message.Message.from_raw("v3.fingerprint.asn", serialized.raw)

    assert deserialized.data == {"asn": "15169"}
