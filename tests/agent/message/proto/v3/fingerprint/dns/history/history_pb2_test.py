"""Unit tests for the DNS history fingerprint protobuf message."""

from ostorlab.agent.message import serializer
from ostorlab.agent.message.proto.v3.fingerprint.dns.history import history_pb2


def testSerialize_whenAllFieldsSet_shouldSerializeAndDeserializeCorrectly() -> None:
    raw = serializer.serialize(
        "v3.fingerprint.dns.history",
        {
            "host": "ostorlab.co",
            "records": [
                {
                    "name": "www.ostorlab.co",
                    "type": "CNAME",
                    "values": [
                        {
                            "value": "cname.vercel-dns.com",
                            "first_seen": "2022-10-12T10:28:42Z",
                            "last_seen": "2024-02-23T21:55:16Z",
                            "seen_count": 44,
                        },
                        {
                            "value": "ostorlab-public-website.netlify.com",
                            "first_seen": "2019-11-25T14:15:48Z",
                            "last_seen": "2022-08-06T11:24:50Z",
                            "seen_count": 46,
                        },
                    ],
                    "truncated": False,
                }
            ],
            "complete": True,
        },
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.dns.history", raw)

    assert isinstance(message, history_pb2.Message)
    assert message.host == "ostorlab.co"
    assert message.complete is True
    assert len(message.records) == 1
    record = message.records[0]
    assert record.name == "www.ostorlab.co"
    assert record.type == "CNAME"
    assert record.HasField("truncated") is True
    assert record.truncated is False
    assert [value.value for value in record.values] == [
        "cname.vercel-dns.com",
        "ostorlab-public-website.netlify.com",
    ]
    latest = record.values[0]
    assert latest.first_seen == "2022-10-12T10:28:42Z"
    assert latest.last_seen == "2024-02-23T21:55:16Z"
    assert latest.seen_count == 44


def testSerialize_whenTheHistoryIsCut_shouldKeepItIncomplete() -> None:
    raw = serializer.serialize(
        "v3.fingerprint.dns.history",
        {
            "host": "example.com",
            "records": [
                {
                    "name": "example.com",
                    "type": "A",
                    "values": [{"value": "203.0.113.7", "seen_count": 3}],
                    "truncated": True,
                }
            ],
            "complete": False,
        },
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.dns.history", raw)

    assert isinstance(message, history_pb2.Message)
    assert message.complete is False
    assert message.records[0].truncated is True
    assert message.records[0].values[0].HasField("first_seen") is False


def testSerialize_whenPeriodSet_shouldSerializeAndDeserializeCorrectly() -> None:
    raw = serializer.serialize(
        "v3.fingerprint.dns.history",
        {
            "host": "ostorlab.co",
            "complete": True,
            "period_from": "2026-10-30T00:00:00Z",
            "period_to": "2026-11-25T08:12:03Z",
        },
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.dns.history", raw)

    assert isinstance(message, history_pb2.Message)
    assert message.period_from == "2026-10-30T00:00:00Z"
    assert message.period_to == "2026-11-25T08:12:03Z"


def testSerialize_whenPeriodCoversTheWholeHistory_shouldKeepPeriodFromUnset() -> None:
    raw = serializer.serialize(
        "v3.fingerprint.dns.history",
        {"host": "ostorlab.co", "period_to": "2026-11-25T08:12:03Z"},
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.dns.history", raw)

    assert isinstance(message, history_pb2.Message)
    assert message.HasField("period_from") is False
    assert message.period_to == "2026-11-25T08:12:03Z"


def testSerialize_whenNoPeriod_shouldKeepPeriodUnset() -> None:
    raw = serializer.serialize(
        "v3.fingerprint.dns.history",
        {"host": "ostorlab.co", "complete": False},
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.dns.history", raw)

    assert isinstance(message, history_pb2.Message)
    assert message.HasField("period_from") is False
    assert message.HasField("period_to") is False
