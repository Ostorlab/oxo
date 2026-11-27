"""Unit tests for the UI call capture protobuf message."""

from ostorlab.agent.message import serializer
from ostorlab.agent.message.proto.v3.capture.ui_call import ui_call_pb2


def testSerialize_whenCapturedAtSet_shouldSerializeAndDeserializeCorrectly() -> None:
    raw = serializer.serialize(
        "v3.capture.ui_call",
        {
            "path": "https://ostorlab.co/",
            "dna": "a41e07",
            "screenshot": b"\xff\xd8\xff\xe0",
            "captured_at": "2019-01-29T22:43:31Z",
        },
    ).SerializeToString()

    message = serializer.deserialize("v3.capture.ui_call", raw)

    assert isinstance(message, ui_call_pb2.Message)
    assert message.path == "https://ostorlab.co/"
    assert message.screenshot == b"\xff\xd8\xff\xe0"
    assert message.captured_at == "2019-01-29T22:43:31Z"


def testSerialize_whenCapturedAtAbsent_shouldKeepItUnset() -> None:
    raw = serializer.serialize(
        "v3.capture.ui_call",
        {"path": "https://ostorlab.co/", "screenshot": b"\xff\xd8\xff\xe0"},
    ).SerializeToString()

    message = serializer.deserialize("v3.capture.ui_call", raw)

    assert isinstance(message, ui_call_pb2.Message)
    assert message.HasField("captured_at") is False


def testSerialize_whenPeriodSet_shouldSerializeAndDeserializeCorrectly() -> None:
    raw = serializer.serialize(
        "v3.capture.ui_call",
        {
            "path": "https://ostorlab.co/",
            "screenshot": b"\xff\xd8\xff\xe0",
            "captured_at": "2026-10-14T09:02:11Z",
            "period_from": "2026-10-01T00:00:00Z",
            "period_to": "2026-11-01T00:00:00Z",
        },
    ).SerializeToString()

    message = serializer.deserialize("v3.capture.ui_call", raw)

    assert isinstance(message, ui_call_pb2.Message)
    assert message.period_from == "2026-10-01T00:00:00Z"
    assert message.period_to == "2026-11-01T00:00:00Z"


def testSerialize_whenPeriodCoversTheWholeHistory_shouldKeepPeriodFromUnset() -> None:
    raw = serializer.serialize(
        "v3.capture.ui_call",
        {
            "path": "https://ostorlab.co/",
            "screenshot": b"\xff\xd8\xff\xe0",
            "period_to": "2019-02-01T00:00:00Z",
        },
    ).SerializeToString()

    message = serializer.deserialize("v3.capture.ui_call", raw)

    assert isinstance(message, ui_call_pb2.Message)
    assert message.HasField("period_from") is False
    assert message.period_to == "2019-02-01T00:00:00Z"


def testSerialize_whenNoPeriod_shouldKeepPeriodUnset() -> None:
    raw = serializer.serialize(
        "v3.capture.ui_call",
        {"path": "https://ostorlab.co/", "screenshot": b"\xff\xd8\xff\xe0"},
    ).SerializeToString()

    message = serializer.deserialize("v3.capture.ui_call", raw)

    assert isinstance(message, ui_call_pb2.Message)
    assert message.HasField("period_from") is False
    assert message.HasField("period_to") is False
