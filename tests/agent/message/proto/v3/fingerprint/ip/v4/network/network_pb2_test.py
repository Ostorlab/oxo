from ostorlab.agent.message import message as agent_message


def testMessageFromData_whenCloudAndBotnetListings_roundTrips() -> None:
    data = {
        "host": "50.16.16.211",
        "version": 4,
        "listings": [
            {"source": "AWS", "category": "cloud", "detail": "EC2 us-east-1"},
            {
                "source": "Feodo Tracker",
                "category": "botnet_c2",
                "detail": "QakBot",
                "last_seen_date": "2026-03-12",
            },
        ],
    }

    serialized = agent_message.Message.from_data("v3.fingerprint.ip.v4.network", data)
    deserialized = agent_message.Message.from_raw(
        "v3.fingerprint.ip.v4.network", serialized.raw
    )

    assert deserialized.data == data
