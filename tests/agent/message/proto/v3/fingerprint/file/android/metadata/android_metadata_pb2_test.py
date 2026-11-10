"""Unit tests for the v3.fingerprint.file.android.metadata message."""

from ostorlab.agent.message import message as agent_message
from ostorlab.agent.message.proto.v3.fingerprint.file.android.metadata import (
    metadata_pb2,
)


def testMessageFromData_whenBuildFieldsProvided_roundTrips() -> None:
    data = {
        "package_name": "com.example.app",
        "permissions": [
            {"name": "android.permission.INTERNET", "protection_levels": ["normal"]}
        ],
        "min_sdk_version": 24,
        "target_sdk_version": 34,
        "signature_schemes": ["v1", "v2", "v3"],
        "signing_certificates": [
            {
                "subject": "Common Name: Example, Organization: Example Inc., Country: US",
                "issuer": "Common Name: Example, Organization: Example Inc., Country: US",
                "serial_number": "1234567890",
                "sha256_fingerprint": "2A:7D:0C:FB:9E:16:29:52",
                "sha1_fingerprint": "AB:CD:EF:01",
                "not_valid_before": "2020-01-01T00:00:00+00:00",
                "not_valid_after": "2050-01-01T00:00:00+00:00",
            }
        ],
        "size": 9437184,
        "md5": "d41d8cd98f00b204e9800998ecf8427e",
        "sha1": "da39a3ee5e6b4b0d3255bfef95601890afd80709",
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "version_name": "10.2.0",
        "version_code": 100200008,
        "label": "Sworkit",
    }

    serialized = agent_message.Message.from_data(
        "v3.fingerprint.file.android.metadata", data
    )
    deserialized = agent_message.Message.from_raw(
        "v3.fingerprint.file.android.metadata", serialized.raw
    )

    assert deserialized.data == data


def testMessage_whenBuildFieldsNotSet_hasNoBuildFields() -> None:
    msg = metadata_pb2.Message()
    msg.package_name = "com.example.app"

    deserialized = metadata_pb2.Message()
    deserialized.ParseFromString(msg.SerializeToString())

    assert deserialized.HasField("min_sdk_version") is False
    assert deserialized.HasField("target_sdk_version") is False
    assert len(deserialized.signature_schemes) == 0
    assert len(deserialized.signing_certificates) == 0
    for field in (
        "size",
        "md5",
        "sha1",
        "sha256",
        "version_name",
        "version_code",
        "label",
    ):
        assert deserialized.HasField(field) is False
