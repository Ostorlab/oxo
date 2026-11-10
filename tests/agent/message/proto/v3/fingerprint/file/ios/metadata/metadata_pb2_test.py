from ostorlab.agent.message import message as agent_message
from ostorlab.agent.message.proto.v3.fingerprint.file.ios.metadata import metadata_pb2


def testMessage_whenCreateWithValidData_shouldSerializeAndDeserializeCorrectly() -> (
    None
):
    msg = metadata_pb2.Message()
    msg.bundle_id = "com.example.test"

    permission = msg.permissions.add()
    permission.name = "camera"
    permission.usage_description = "App needs camera access"

    permission2 = msg.permissions.add()
    permission2.name = "location"
    permission2.usage_description = "App needs location access"

    serialized = msg.SerializeToString()
    deserialized_msg = metadata_pb2.Message()
    deserialized_msg.ParseFromString(serialized)

    assert deserialized_msg.bundle_id == "com.example.test"
    assert len(deserialized_msg.permissions) == 2
    assert deserialized_msg.permissions[0].name == "camera"
    assert (
        deserialized_msg.permissions[0].usage_description == "App needs camera access"
    )
    assert deserialized_msg.permissions[1].name == "location"
    assert (
        deserialized_msg.permissions[1].usage_description == "App needs location access"
    )


def testMessage_whenCreateEmpty_shouldHaveDefaultValues() -> None:
    msg = metadata_pb2.Message()

    assert msg.bundle_id == ""
    assert len(msg.permissions) == 0


def testMessage_whenSerializeEmpty_shouldDeserializeToEmpty() -> None:
    msg = metadata_pb2.Message()

    serialized = msg.SerializeToString()
    deserialized_msg = metadata_pb2.Message()
    deserialized_msg.ParseFromString(serialized)

    assert deserialized_msg.bundle_id == ""
    assert len(deserialized_msg.permissions) == 0


def testMessageFromData_whenBuildFieldsProvided_roundTrips() -> None:
    data = {
        "bundle_id": "com.example.app",
        "permissions": [
            {"name": "Camera", "usage_description": "App needs camera access"}
        ],
        "minimum_os_version": "14.0",
        "team_id": "K8WKU3XKKY",
        "entitlements": [
            {"name": "aps-environment", "values": ["production"]},
            {"name": "get-task-allow", "values": ["false"]},
            {
                "name": "com.apple.developer.associated-domains",
                "values": ["applinks:example.com", "webcredentials:example.com"],
            },
        ],
        "associated_domains": ["applinks:example.com", "webcredentials:example.com"],
        "url_schemes": ["com.example.app", "fb1234567890"],
        "privacy_manifests": [
            {
                "path": "Payload/Runner.app/Frameworks/AirshipKit.framework/PrivacyInfo.xcprivacy",
                "owner": "AirshipKit.framework",
                "owner_type": "framework",
                "tracking": False,
                "tracking_domains": ["tracking.example.com"],
                "collected_data_types": [
                    {
                        "type": "NSPrivacyCollectedDataTypeProductInteraction",
                        "linked": False,
                        "tracking": False,
                        "purposes": ["NSPrivacyCollectedDataTypePurposeAnalytics"],
                    }
                ],
                "accessed_api_types": [
                    {
                        "type": "NSPrivacyAccessedAPICategoryUserDefaults",
                        "reasons": ["CA92.1"],
                    }
                ],
            }
        ],
        "size": 52428800,
        "md5": "d41d8cd98f00b204e9800998ecf8427e",
        "sha1": "da39a3ee5e6b4b0d3255bfef95601890afd80709",
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "version_name": "2.4.1",
        "version_code": "241",
        "label": "Example",
    }

    serialized = agent_message.Message.from_data(
        "v3.fingerprint.file.ios.metadata", data
    )
    deserialized = agent_message.Message.from_raw(
        "v3.fingerprint.file.ios.metadata", serialized.raw
    )

    assert deserialized.data == data
