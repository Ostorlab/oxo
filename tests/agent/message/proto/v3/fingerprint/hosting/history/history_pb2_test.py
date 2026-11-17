"""Unit tests for the hosting history fingerprint protobuf message."""

from ostorlab.agent.message import serializer
from ostorlab.agent.message.proto.v3.fingerprint.hosting.history import history_pb2


def testSerialize_whenAllFieldsSet_shouldSerializeAndDeserializeCorrectly() -> None:
    raw = serializer.serialize(
        "v3.fingerprint.hosting.history",
        {
            "host": "ostorlab.co",
            "periods": [
                {
                    "owner": "Vercel, Inc",
                    "first_seen": "2023-05-27T06:36:59Z",
                    "last_seen": "2024-02-26T06:05:40Z",
                    "addresses": ["76.76.21.21"],
                },
                {
                    "owner": "OVH SAS",
                    "first_seen": "2016-10-28T12:03:24Z",
                    "last_seen": "2019-07-23T12:41:24Z",
                    "addresses": ["164.132.45.228", "5.196.22.220"],
                },
            ],
            "complete": True,
        },
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.hosting.history", raw)

    assert isinstance(message, history_pb2.Message)
    assert message.host == "ostorlab.co"
    assert message.complete is True
    assert [period.owner for period in message.periods] == ["Vercel, Inc", "OVH SAS"]
    ovh = message.periods[1]
    assert ovh.first_seen == "2016-10-28T12:03:24Z"
    assert ovh.last_seen == "2019-07-23T12:41:24Z"
    assert list(ovh.addresses) == ["164.132.45.228", "5.196.22.220"]


def testSerialize_whenNoPeriod_shouldKeepItIncompleteAndEmpty() -> None:
    raw = serializer.serialize(
        "v3.fingerprint.hosting.history",
        {"host": "example.com", "periods": [], "complete": False},
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.hosting.history", raw)

    assert isinstance(message, history_pb2.Message)
    assert len(message.periods) == 0
    assert message.HasField("complete") is True
    assert message.complete is False
