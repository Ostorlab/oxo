"""Tests for message module."""

from ostorlab.agent.message import message


def testMessageSerializeDeserialize_whenSelectorIsValid_generatesProperProto():
    """Test message proper serialization from a dict object to a protobuf based on the selector."""
    serialized = message.Message.from_data('v3.fingerprint.file', {
        'path': '/etc/hosts',
    })
    deserialized = message.Message.from_raw('v3.fingerprint.file', serialized.raw)

    assert isinstance(serialized.raw, bytes)
    assert deserialized.data.path == '/etc/hosts'
