"""Unit tests for the security headers fingerprint protobuf message."""

from ostorlab.agent.message import serializer
from ostorlab.agent.message.proto.v3.fingerprint.domain_name.service.http.security_headers import (
    security_headers_pb2,
)


def testSerialize_whenAllFieldsSet_shouldSerializeAndDeserializeCorrectly() -> None:
    raw = serializer.serialize(
        "v3.fingerprint.domain_name.service.http.security_headers",
        {
            "name": "ostorlab.co",
            "port": 443,
            "schema": "https",
            "grade": "C",
            "score": 50,
            "tests_passed": 5,
            "tests_failed": 5,
            "checks": [
                {
                    "name": "strict-transport-security",
                    "passed": True,
                    "result": "hsts-implemented-max-age-at-least-six-months",
                    "score_modifier": 0,
                },
                {
                    "name": "content-security-policy",
                    "passed": False,
                    "result": "csp-not-implemented",
                    "score_modifier": -25,
                },
            ],
            "headers": [
                {"name": "strict-transport-security", "value": "max-age=31536000"},
                {"name": "x-frame-options", "value": "SAMEORIGIN"},
            ],
        },
    ).SerializeToString()

    message = serializer.deserialize(
        "v3.fingerprint.domain_name.service.http.security_headers", raw
    )

    assert isinstance(message, security_headers_pb2.Message)
    assert message.name == "ostorlab.co"
    assert message.port == 443
    assert message.schema == "https"
    assert message.grade == "C"
    assert message.score == 50
    assert message.tests_passed == 5
    assert message.tests_failed == 5
    assert [check.name for check in message.checks] == [
        "strict-transport-security",
        "content-security-policy",
    ]
    assert message.checks[0].passed is True
    assert message.checks[0].result == "hsts-implemented-max-age-at-least-six-months"
    assert message.checks[1].passed is False
    assert message.checks[1].score_modifier == -25
    assert [(header.name, header.value) for header in message.headers] == [
        ("strict-transport-security", "max-age=31536000"),
        ("x-frame-options", "SAMEORIGIN"),
    ]


def testSerialize_whenPageSetsNoSecurityHeader_shouldKeepTheGradeAndNoHeader() -> None:
    raw = serializer.serialize(
        "v3.fingerprint.domain_name.service.http.security_headers",
        {
            "name": "example.com",
            "port": 443,
            "schema": "https",
            "grade": "F",
            "score": 0,
            "checks": [
                {
                    "name": "x-content-type-options",
                    "passed": False,
                    "result": "x-content-type-options-not-implemented",
                    "score_modifier": -5,
                }
            ],
        },
    ).SerializeToString()

    message = serializer.deserialize(
        "v3.fingerprint.domain_name.service.http.security_headers", raw
    )

    assert isinstance(message, security_headers_pb2.Message)
    assert message.grade == "F"
    assert message.HasField("score") is True
    assert message.score == 0
    assert list(message.headers) == []
