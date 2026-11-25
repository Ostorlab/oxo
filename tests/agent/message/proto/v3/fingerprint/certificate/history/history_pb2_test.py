"""Unit tests for the certificate history fingerprint protobuf message."""

import pytest

from ostorlab.agent.message import serializer
from ostorlab.agent.message.proto.v3.fingerprint.certificate.history import history_pb2


def testSerialize_whenAllFieldsSet_shouldSerializeAndDeserializeCorrectly() -> None:
    raw = serializer.serialize(
        "v3.fingerprint.certificate.history",
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
                    "names": ["ostorlab.co"],
                    "x509": {
                        "serial_number": "000005D06BBEA210D5D62651DB3859549B415BDE",
                        "issuer": {"C": "US", "O": "Let's Encrypt", "CN": "YR1"},
                        "validity": {"not_before": 1784638502, "not_after": 1792414501},
                    },
                },
                {
                    "crtsh_id": 26492929997,
                    "names": ["ostorlab.co"],
                    "x509": {
                        "serial_number": "00000685EA979533C3DCE9820D03945DD632A9D0",
                        "issuer": {"C": "US", "O": "Let's Encrypt", "CN": "R12"},
                        "validity": {"not_before": 1779284390, "not_after": 1787060389},
                    },
                },
            ],
            "data_up_to": "2026-10-20T21:51:36Z",
            "complete": True,
            "search_url": "https://crt.sh/?q=ostorlab.co",
        },
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.certificate.history", raw)

    assert isinstance(message, history_pb2.Message)
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
    assert newest.x509.issuer.CN == "YR1"
    assert newest.x509.serial_number == "000005D06BBEA210D5D62651DB3859549B415BDE"
    assert newest.x509.validity.not_before == 1784638502
    assert newest.x509.validity.not_after == 1792414501
    assert list(newest.names) == ["ostorlab.co"]
    assert message.data_up_to == "2026-10-20T21:51:36Z"
    assert message.complete is True
    assert len(message.missing_ranges) == 0
    assert message.search_url == "https://crt.sh/?q=ostorlab.co"


def testSerialize_whenHostIsAnIp_shouldKeepEveryNameOnTheCertificate() -> None:
    raw = serializer.serialize(
        "v3.fingerprint.certificate.history",
        {
            "host": "203.0.113.7",
            "certificate_count": 1,
            "host_certificate_count": 1,
            "certificates": [
                {
                    "crtsh_id": 1,
                    "names": ["203.0.113.7", "www.example.com"],
                }
            ],
            "complete": True,
            "search_url": "https://crt.sh/?q=203.0.113.7",
        },
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.certificate.history", raw)

    assert isinstance(message, history_pb2.Message)
    assert message.host == "203.0.113.7"
    assert message.host_certificate_count == message.certificate_count
    assert list(message.certificates[0].names) == ["203.0.113.7", "www.example.com"]


def testSerialize_whenSomeRangesTimedOut_shouldKeepTheMissingRanges() -> None:
    raw = serializer.serialize(
        "v3.fingerprint.certificate.history",
        {
            "host": "example.com",
            "certificate_count": 155907,
            "host_certificate_count": 46,
            "complete": False,
            "missing_ranges": ["2023-01-01/2024-01-01", "2024-01-01/2025-01-01"],
        },
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.certificate.history", raw)

    assert isinstance(message, history_pb2.Message)
    assert message.HasField("complete") is True
    assert message.complete is False
    assert list(message.missing_ranges) == [
        "2023-01-01/2024-01-01",
        "2024-01-01/2025-01-01",
    ]


def testSerialize_whenNoCertificate_shouldKeepTheZeroCountWithoutDates() -> None:
    raw = serializer.serialize(
        "v3.fingerprint.certificate.history",
        {
            "host": "example.com",
            "certificate_count": 0,
            "host_certificate_count": 0,
            "complete": True,
            "search_url": "https://crt.sh/?q=example.com",
        },
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.certificate.history", raw)

    assert isinstance(message, history_pb2.Message)
    assert message.HasField("certificate_count") is True
    assert message.certificate_count == 0
    assert message.HasField("first_issued") is False
    assert message.HasField("last_issued") is False
    assert len(message.issuers) == 0
    assert len(message.certificates) == 0


def testSerialize_whenACertificateHasItsX509_shouldSerializeAndDeserializeCorrectly() -> (
    None
):
    raw = serializer.serialize(
        "v3.fingerprint.certificate.history",
        {
            "host": "ostorlab.co",
            "certificates": [
                {
                    "crtsh_id": 30037303884,
                    "names": ["ostorlab.co"],
                    "x509": {
                        "version_number": 3,
                        "serial_number": "0000055CE6AD4438E52F1EAE15DA7829A2A89F04",
                        "issuer": {"C": "US", "O": "Let's Encrypt", "CN": "YR1"},
                        "subject": {"CN": "ostorlab.co"},
                        "validity": {"not_before": 1790100731, "not_after": 1797876730},
                        "public_key": {"public_key_algorithm": "RSA Public Key"},
                        "signature": {"signature_algorithm": "sha256"},
                        "computed_fingerprint": [
                            {
                                "fingerprint_algorithm": "sha256",
                                "fingerprint_value": "D0D008F4695F2B3C0DDB06326845812D4AD8E465E81009E7E717433CCE3C280F",
                            }
                        ],
                        "extensions": [{"oid": "2.5.29.17", "value": "ostorlab.co"}],
                    },
                }
            ],
        },
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.certificate.history", raw)

    assert isinstance(message, history_pb2.Message)
    x509 = message.certificates[0].x509
    assert x509.serial_number == "0000055CE6AD4438E52F1EAE15DA7829A2A89F04"
    assert x509.issuer.O == "Let's Encrypt"
    assert x509.issuer.CN == "YR1"
    assert x509.subject.CN == "ostorlab.co"
    assert x509.validity.not_before == 1790100731
    assert x509.public_key.public_key_algorithm == "RSA Public Key"
    assert x509.signature.signature_algorithm == "sha256"
    assert x509.computed_fingerprint[0].fingerprint_value == (
        "D0D008F4695F2B3C0DDB06326845812D4AD8E465E81009E7E717433CCE3C280F"
    )
    assert x509.extensions[0].value == "ostorlab.co"


def testSerialize_whenACertificateHasNoX509_shouldKeepItUnset() -> None:
    raw = serializer.serialize(
        "v3.fingerprint.certificate.history",
        {
            "host": "ostorlab.co",
            "certificates": [{"crtsh_id": 28125128965, "names": ["ostorlab.co"]}],
        },
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.certificate.history", raw)

    assert isinstance(message, history_pb2.Message)
    assert message.certificates[0].HasField("x509") is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("issuer", "C=US, O=Let's Encrypt, CN=YR1"),
        ("serial_number", "055ce6ad4438e52f1eae15da7829a2a89f04"),
        ("not_before", "2026-09-22T18:12:11Z"),
        ("not_after", "2026-12-21T18:12:10Z"),
    ],
)
def testSerialize_whenACertificateHasAFieldOfItsX509_shouldRaiseSerializationError(
    field: str, value: str
) -> None:
    with pytest.raises(serializer.SerializationError):
        serializer.serialize(
            "v3.fingerprint.certificate.history",
            {"host": "ostorlab.co", "certificates": [{"crtsh_id": 1, field: value}]},
        )


def testSerialize_whenPeriodSet_shouldSerializeAndDeserializeCorrectly() -> None:
    raw = serializer.serialize(
        "v3.fingerprint.certificate.history",
        {
            "host": "ostorlab.co",
            "data_up_to": "2026-11-24T21:51:36Z",
            "complete": True,
            "period_from": "2026-10-30T00:00:00Z",
            "period_to": "2026-11-24T21:51:36Z",
        },
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.certificate.history", raw)

    assert isinstance(message, history_pb2.Message)
    assert message.period_from == "2026-10-30T00:00:00Z"
    assert message.period_to == "2026-11-24T21:51:36Z"


def testSerialize_whenPeriodCoversTheWholeHistory_shouldKeepPeriodFromUnset() -> None:
    raw = serializer.serialize(
        "v3.fingerprint.certificate.history",
        {"host": "ostorlab.co", "period_to": "2026-11-24T21:51:36Z"},
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.certificate.history", raw)

    assert isinstance(message, history_pb2.Message)
    assert message.HasField("period_from") is False
    assert message.period_to == "2026-11-24T21:51:36Z"


def testSerialize_whenNoPeriod_shouldKeepPeriodUnset() -> None:
    raw = serializer.serialize(
        "v3.fingerprint.certificate.history",
        {"host": "ostorlab.co", "complete": False},
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.certificate.history", raw)

    assert isinstance(message, history_pb2.Message)
    assert message.HasField("period_from") is False
    assert message.HasField("period_to") is False
