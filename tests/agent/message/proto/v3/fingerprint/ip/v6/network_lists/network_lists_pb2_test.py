from ostorlab.agent.message import message as agent_message


def testMessageFromData_whenIpv6TorExit_roundTrips() -> None:
    data = {
        "host": "2001:67c:e60:c0c:192:42:116:16",
        "version": 6,
        "listings": [{"source": "Tor Project", "category": "tor_exit_node"}],
    }

    serialized = agent_message.Message.from_data(
        "v3.fingerprint.ip.v6.network_lists", data
    )
    deserialized = agent_message.Message.from_raw(
        "v3.fingerprint.ip.v6.network_lists", serialized.raw
    )

    assert deserialized.data == data
