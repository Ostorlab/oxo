"""Tests for the v3.fingerprint.file.ios.backend message."""

from ostorlab.agent.message import message


def testBackendMessage_whenUrlIsSet_keepsTheUrlAndTheHost() -> None:
    data = {
        "path": "assets/index.android.bundle",
        "bundle_id": "com.example.app",
        "host": "api.example.com",
        "url": "https://api.example.com/v1",
    }

    msg = message.Message.from_data("v3.fingerprint.file.ios.backend", data=data)
    parsed = message.Message.from_raw("v3.fingerprint.file.ios.backend", msg.raw)

    assert parsed.data["host"] == "api.example.com"
    assert parsed.data["url"] == "https://api.example.com/v1"


def testBackendMessage_whenUrlIsNotSet_leavesItOut() -> None:
    data = {"bundle_id": "com.example.app", "host": "api.example.com"}

    msg = message.Message.from_data("v3.fingerprint.file.ios.backend", data=data)
    parsed = message.Message.from_raw("v3.fingerprint.file.ios.backend", msg.raw)

    assert "url" not in parsed.data
