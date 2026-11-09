from ostorlab.agent.message import message as agent_message


def testMessageFromData_whenReportedIp_roundTrips() -> None:
    data = {
        "host": "185.220.101.1",
        "version": 4,
        "reports": [
            {
                "source": "AbuseIPDB",
                "score": 100,
                "report_count": 412,
                "reporter_count": 97,
                "last_reported_date": "2026-11-08T21:14:03+00:00",
                "categories": ["ssh", "brute_force", "port_scan"],
            }
        ],
    }

    serialized = agent_message.Message.from_data(
        "v3.fingerprint.ip.v4.reputation", data
    )
    deserialized = agent_message.Message.from_raw(
        "v3.fingerprint.ip.v4.reputation", serialized.raw
    )

    assert deserialized.data == data


def testMessageFromData_whenNeverReported_keepsTheZeroScore() -> None:
    data = {
        "host": "8.8.8.8",
        "version": 4,
        "reports": [{"source": "AbuseIPDB", "score": 0, "report_count": 0}],
    }

    serialized = agent_message.Message.from_data(
        "v3.fingerprint.ip.v4.reputation", data
    )
    deserialized = agent_message.Message.from_raw(
        "v3.fingerprint.ip.v4.reputation", serialized.raw
    )

    assert deserialized.data == data
