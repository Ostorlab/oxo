from ostorlab.agent.message import message as agent_message


def testMessageFromData_whenPackerFound_roundTrips() -> None:
    data = {
        "package_name": "com.example.app",
        "name": "Jiagu",
        "category": "packer",
        "detail": "classes.dex",
    }

    serialized = agent_message.Message.from_data(
        "v3.fingerprint.file.android.obfuscation", data
    )
    deserialized = agent_message.Message.from_raw(
        "v3.fingerprint.file.android.obfuscation", serialized.raw
    )

    assert deserialized.data == data
