from ostorlab.agent.message import message as agent_message


def testMessageFromData_whenCloudAndListingsProvided_roundTrips() -> None:
    data = {
        "host": "50.16.16.211",
        "version": 4,
        "cloud": {
            "provider": "AWS",
            "service": "EC2",
            "region": "us-east-1",
            "cidr": "50.16.0.0/15",
        },
        "listings": [
            {
                "source": "Feodo Tracker",
                "category": "botnet_c2",
                "detail": "QakBot",
                "last_seen_date": "2026-03-12",
            }
        ],
    }

    serialized = agent_message.Message.from_data("v3.asset.ip.v4.network_lists", data)
    deserialized = agent_message.Message.from_raw(
        "v3.asset.ip.v4.network_lists", serialized.raw
    )

    assert deserialized.data == data
