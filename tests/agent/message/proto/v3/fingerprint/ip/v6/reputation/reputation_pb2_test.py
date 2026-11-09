from ostorlab.agent.message import message as agent_message


def testMessageFromData_whenIpv6Reported_roundTrips() -> None:
    data = {
        "host": "2001:db8::1",
        "version": 6,
        "reports": [
            {"source": "AbuseIPDB", "score": 35, "categories": ["web_app_attack"]}
        ],
    }

    serialized = agent_message.Message.from_data(
        "v3.fingerprint.ip.v6.reputation", data
    )
    deserialized = agent_message.Message.from_raw(
        "v3.fingerprint.ip.v6.reputation", serialized.raw
    )

    assert deserialized.data == data
