"""Unit tests for the web archive fingerprint protobuf message."""

from ostorlab.agent.message import serializer
from ostorlab.agent.message.proto.v3.fingerprint.domain_name.web_archive import (
    web_archive_pb2,
)


def testSerialize_whenAllFieldsSet_shouldSerializeAndDeserializeCorrectly() -> None:
    raw = serializer.serialize(
        "v3.fingerprint.domain_name.web_archive",
        {
            "name": "ostorlab.co",
            "first_archived": "2018-01-17T18:24:04Z",
            "last_archived": "2026-10-12T15:45:14Z",
            "snapshot_count": 186,
            "first_snapshot_url": "https://web.archive.org/web/20180117182404/ostorlab.co",
            "last_snapshot_url": "https://web.archive.org/web/20261012154514/ostorlab.co",
            "calendar_url": "https://web.archive.org/web/*/ostorlab.co",
        },
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.domain_name.web_archive", raw)

    assert isinstance(message, web_archive_pb2.Message)
    assert message.name == "ostorlab.co"
    assert message.first_archived == "2018-01-17T18:24:04Z"
    assert message.last_archived == "2026-10-12T15:45:14Z"
    assert message.snapshot_count == 186
    assert (
        message.first_snapshot_url
        == "https://web.archive.org/web/20180117182404/ostorlab.co"
    )
    assert (
        message.last_snapshot_url
        == "https://web.archive.org/web/20261012154514/ostorlab.co"
    )
    assert message.calendar_url == "https://web.archive.org/web/*/ostorlab.co"


def testSerialize_whenNeverArchived_shouldKeepTheZeroCountWithoutDates() -> None:
    raw = serializer.serialize(
        "v3.fingerprint.domain_name.web_archive",
        {
            "name": "example.com",
            "snapshot_count": 0,
            "calendar_url": "https://web.archive.org/web/*/example.com",
        },
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.domain_name.web_archive", raw)

    assert isinstance(message, web_archive_pb2.Message)
    assert message.HasField("snapshot_count") is True
    assert message.snapshot_count == 0
    assert message.HasField("first_archived") is False
    assert message.HasField("last_archived") is False
    assert message.HasField("first_snapshot_url") is False
    assert message.calendar_url == "https://web.archive.org/web/*/example.com"
