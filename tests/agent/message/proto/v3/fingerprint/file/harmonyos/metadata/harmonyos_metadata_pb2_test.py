"""Unit tests for the v3.fingerprint.file.harmonyos.metadata message."""

from ostorlab.agent.message import message as agent_message


def testMessageFromData_whenPermissionsProvided_roundTrips() -> None:
    data = {
        "path": "entry-default.hap",
        "bundle_name": "com.example.app",
        "permissions": [
            {"name": "ohos.permission.INTERNET"},
            {
                "name": "ohos.permission.CAMERA",
                "reason": "$string:reason_camera",
                "used_scene_abilities": ["EntryAbility"],
                "used_scene_when": "inuse",
            },
        ],
        "min_api_version": 12,
        "target_api_version": 14,
    }

    serialized = agent_message.Message.from_data(
        "v3.fingerprint.file.harmonyos.metadata", data
    )
    deserialized = agent_message.Message.from_raw(
        "v3.fingerprint.file.harmonyos.metadata", serialized.raw
    )

    assert deserialized.data == data
