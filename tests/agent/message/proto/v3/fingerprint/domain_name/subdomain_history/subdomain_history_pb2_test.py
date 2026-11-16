"""Unit tests for the subdomain history fingerprint protobuf message."""

from ostorlab.agent.message import serializer
from ostorlab.agent.message.proto.v3.fingerprint.domain_name.subdomain_history import (
    subdomain_history_pb2,
)


def testSerialize_whenAllFieldsSet_shouldSerializeAndDeserializeCorrectly() -> None:
    raw = serializer.serialize(
        "v3.fingerprint.domain_name.subdomain_history",
        {
            "name": "ostorlab.co",
            "subdomain_count": 18,
            "subdomains": [
                {
                    "name": "api.ostorlab.co",
                    "first_seen": "2020-02-11T20:32:45Z",
                    "last_seen": "2026-07-27T15:25:32Z",
                    "last_expires": "2026-10-25T16:20:26Z",
                    "certificate_count": 45,
                },
                {
                    "name": "bus.ostorlab.co",
                    "first_seen": "2021-11-09T18:24:29Z",
                    "last_seen": "2022-03-12T17:36:17Z",
                    "last_expires": "2022-06-10T17:36:16Z",
                    "certificate_count": 4,
                },
            ],
            "part": 1,
            "part_count": 1,
            "data_up_to": "2026-10-20T21:51:36Z",
            "complete": True,
        },
    ).SerializeToString()

    message = serializer.deserialize(
        "v3.fingerprint.domain_name.subdomain_history", raw
    )

    assert isinstance(message, subdomain_history_pb2.Message)
    assert message.name == "ostorlab.co"
    assert message.subdomain_count == 18
    assert len(message.subdomains) == 2
    api = message.subdomains[0]
    assert api.name == "api.ostorlab.co"
    assert api.first_seen == "2020-02-11T20:32:45Z"
    assert api.last_seen == "2026-07-27T15:25:32Z"
    assert api.last_expires == "2026-10-25T16:20:26Z"
    assert api.certificate_count == 45
    assert message.subdomains[1].name == "bus.ostorlab.co"
    assert message.part == 1
    assert message.part_count == 1
    assert message.data_up_to == "2026-10-20T21:51:36Z"
    assert message.complete is True


def testSerialize_whenSplitInParts_shouldKeepThePartAndTheTotalCount() -> None:
    raw = serializer.serialize(
        "v3.fingerprint.domain_name.subdomain_history",
        {
            "name": "example.com",
            "subdomain_count": 4100,
            "subdomains": [
                {
                    "name": "*.dev.example.com",
                    "first_seen": "2024-03-01T08:00:00Z",
                    "last_seen": "2026-09-01T08:00:00Z",
                    "last_expires": "2026-11-30T08:00:00Z",
                    "certificate_count": 12,
                }
            ],
            "part": 2,
            "part_count": 3,
            "complete": False,
        },
    ).SerializeToString()

    message = serializer.deserialize(
        "v3.fingerprint.domain_name.subdomain_history", raw
    )

    assert isinstance(message, subdomain_history_pb2.Message)
    assert message.subdomain_count == 4100
    assert len(message.subdomains) == 1
    assert message.subdomains[0].name == "*.dev.example.com"
    assert message.part == 2
    assert message.part_count == 3
    assert message.HasField("complete") is True
    assert message.complete is False
