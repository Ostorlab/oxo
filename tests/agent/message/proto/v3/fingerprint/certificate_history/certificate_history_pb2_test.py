"""Unit tests for the certificate history fingerprint protobuf message."""

from ostorlab.agent.message import serializer
from ostorlab.agent.message.proto.v3.fingerprint.certificate_history import (
    certificate_history_pb2,
)


def testSerialize_whenAllFieldsSet_shouldSerializeAndDeserializeCorrectly() -> None:
    raw = serializer.serialize(
        "v3.fingerprint.certificate_history",
        {
            "host": "ostorlab.co",
            "certificate_count": 392,
            "host_certificate_count": 60,
            "first_issued": "2015-04-14T00:00:00Z",
            "last_issued": "2026-10-06T00:55:23Z",
            "issuers": [
                {
                    "name": "C=US, O=Google Trust Services, CN=WR3",
                    "first_issued": "2024-07-30T07:36:41Z",
                    "last_issued": "2026-10-06T00:55:23Z",
                    "certificate_count": 29,
                },
                {
                    "name": "C=US, O=Let's Encrypt, CN=YR1",
                    "first_issued": "2026-06-30T19:38:52Z",
                    "last_issued": "2026-09-14T12:05:10Z",
                    "certificate_count": 6,
                },
            ],
            "certificates": [
                {
                    "crtsh_id": 28125128965,
                    "issuer": "C=US, O=Let's Encrypt, CN=YR1",
                    "serial_number": "05d06bbea210d5d62651db3859549b415bde",
                    "not_before": "2026-07-21T12:55:02Z",
                    "not_after": "2026-10-19T12:55:01Z",
                    "names": ["ostorlab.co"],
                },
                {
                    "crtsh_id": 26492929997,
                    "issuer": "C=US, O=Let's Encrypt, CN=R12",
                    "serial_number": "0685ea979533c3dce9820d03945dd632a9d0",
                    "not_before": "2026-05-20T13:39:50Z",
                    "not_after": "2026-08-18T13:39:49Z",
                    "names": ["ostorlab.co"],
                },
            ],
            "data_up_to": "2026-10-20T21:51:36Z",
            "complete": True,
            "search_url": "https://crt.sh/?q=ostorlab.co",
        },
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.certificate_history", raw)

    assert isinstance(message, certificate_history_pb2.Message)
    assert message.host == "ostorlab.co"
    assert message.certificate_count == 392
    assert message.host_certificate_count == 60
    assert message.first_issued == "2015-04-14T00:00:00Z"
    assert message.last_issued == "2026-10-06T00:55:23Z"
    assert len(message.issuers) == 2
    assert message.issuers[0].name == "C=US, O=Google Trust Services, CN=WR3"
    assert message.issuers[0].first_issued == "2024-07-30T07:36:41Z"
    assert message.issuers[0].last_issued == "2026-10-06T00:55:23Z"
    assert message.issuers[0].certificate_count == 29
    assert len(message.certificates) == 2
    newest = message.certificates[0]
    assert newest.crtsh_id == 28125128965
    assert newest.issuer == "C=US, O=Let's Encrypt, CN=YR1"
    assert newest.serial_number == "05d06bbea210d5d62651db3859549b415bde"
    assert newest.not_before == "2026-07-21T12:55:02Z"
    assert newest.not_after == "2026-10-19T12:55:01Z"
    assert list(newest.names) == ["ostorlab.co"]
    assert message.data_up_to == "2026-10-20T21:51:36Z"
    assert message.complete is True
    assert len(message.missing_ranges) == 0
    assert message.search_url == "https://crt.sh/?q=ostorlab.co"


def testSerialize_whenHostIsAnIp_shouldKeepEveryNameOnTheCertificate() -> None:
    raw = serializer.serialize(
        "v3.fingerprint.certificate_history",
        {
            "host": "203.0.113.7",
            "certificate_count": 1,
            "host_certificate_count": 1,
            "certificates": [
                {
                    "crtsh_id": 1,
                    "issuer": "C=US, O=Let's Encrypt, CN=YE1",
                    "serial_number": "0a1b2c",
                    "not_before": "2026-09-01T08:00:00Z",
                    "not_after": "2026-09-07T08:00:00Z",
                    "names": ["203.0.113.7", "www.example.com"],
                }
            ],
            "complete": True,
            "search_url": "https://crt.sh/?q=203.0.113.7",
        },
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.certificate_history", raw)

    assert isinstance(message, certificate_history_pb2.Message)
    assert message.host == "203.0.113.7"
    assert message.host_certificate_count == message.certificate_count
    assert list(message.certificates[0].names) == ["203.0.113.7", "www.example.com"]


def testSerialize_whenSomeRangesTimedOut_shouldKeepTheMissingRanges() -> None:
    raw = serializer.serialize(
        "v3.fingerprint.certificate_history",
        {
            "host": "example.com",
            "certificate_count": 155907,
            "host_certificate_count": 46,
            "complete": False,
            "missing_ranges": ["2023-01-01/2024-01-01", "2024-01-01/2025-01-01"],
        },
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.certificate_history", raw)

    assert isinstance(message, certificate_history_pb2.Message)
    assert message.HasField("complete") is True
    assert message.complete is False
    assert list(message.missing_ranges) == [
        "2023-01-01/2024-01-01",
        "2024-01-01/2025-01-01",
    ]


def testSerialize_whenNoCertificate_shouldKeepTheZeroCountWithoutDates() -> None:
    raw = serializer.serialize(
        "v3.fingerprint.certificate_history",
        {
            "host": "example.com",
            "certificate_count": 0,
            "host_certificate_count": 0,
            "complete": True,
            "search_url": "https://crt.sh/?q=example.com",
        },
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.certificate_history", raw)

    assert isinstance(message, certificate_history_pb2.Message)
    assert message.HasField("certificate_count") is True
    assert message.certificate_count == 0
    assert message.HasField("first_issued") is False
    assert message.HasField("last_issued") is False
    assert len(message.issuers) == 0
    assert len(message.certificates) == 0
