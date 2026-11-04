from ostorlab.agent.message import message as agent_message


def testMessageFromData_whenDomainConfigsProvided_roundTrips() -> None:
    data = {
        "path": "res/xml/network_security_config.xml",
        "package_name": "com.example.app",
        "base_cleartext_traffic_permitted": False,
        "base_trust_anchors": ["system"],
        "domain_configs": [
            {
                "domains": [{"name": "example.com", "include_subdomains": True}],
                "cleartext_traffic_permitted": True,
                "trust_anchors": ["@raw/my_ca"],
                "pins": ["SHA-256/7HIpactkIAq2Y49orFOOQKurWxmmSFZhBCoQYcRhJ3Y="],
                "pin_expiration": "2027-01-01",
            }
        ],
        "debug_trust_anchors": ["user"],
    }

    serialized = agent_message.Message.from_data(
        "v3.fingerprint.file.android.network_security", data
    )
    deserialized = agent_message.Message.from_raw(
        "v3.fingerprint.file.android.network_security", serialized.raw
    )

    assert deserialized.data == data
