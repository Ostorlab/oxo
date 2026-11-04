from ostorlab.agent.message import message as agent_message


def testMessageFromData_whenIspAndNetworkFlagsProvided_roundTrips() -> None:
    data = {
        "host": "2600:1f18::1",
        "version": 6,
        "country_code": "US",
        "isp": "Amazon.com, Inc.",
        "org": "AWS EC2 (us-east-1)",
        "mobile": False,
        "proxy": False,
        "hosting": True,
    }

    serialized = agent_message.Message.from_data("v3.asset.ip.v6.geolocation", data)
    deserialized = agent_message.Message.from_raw(
        "v3.asset.ip.v6.geolocation", serialized.raw
    )

    assert deserialized.data == data
