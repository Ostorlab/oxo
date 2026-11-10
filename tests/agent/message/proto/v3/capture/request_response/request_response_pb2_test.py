"""Unit tests for the request_response capture protobuf message."""

from ostorlab.agent.message import serializer
from ostorlab.agent.message.proto.v3.capture.request_response import (
    request_response_pb2,
)


def testSerialize_whenPageUrlSet_shouldSerializeAndDeserializeCorrectly() -> None:
    raw = serializer.serialize(
        "v3.capture.request_response",
        {
            "page_url": "https://www.ostorlab.co",
            "request": {
                "method": "GET",
                "url": "https://static.hotjar.com/c/hotjar-6545586.js?sv=6",
                "headers": [{"name": "referer", "value": "https://ostorlab.co/"}],
            },
            "response": {
                "url": "https://static.hotjar.com/c/hotjar-6545586.js?sv=6",
                "status": 200,
                "headers": [
                    {
                        "name": "content-type",
                        "value": "application/javascript; charset=UTF-8",
                    }
                ],
                "remote_ip": "52.222.132.38",
                "remote_port": 443,
                "body": b"window.hjSiteSettings = {};",
            },
        },
    ).SerializeToString()

    message = serializer.deserialize("v3.capture.request_response", raw)

    assert isinstance(message, request_response_pb2.Message)
    assert message.page_url == "https://www.ostorlab.co"
    assert message.request.url == "https://static.hotjar.com/c/hotjar-6545586.js?sv=6"
    assert message.request.headers[0].value == "https://ostorlab.co/"
    assert message.response.status == 200
    assert message.response.remote_ip == "52.222.132.38"
    assert message.response.body == b"window.hjSiteSettings = {};"


def testSerialize_whenPageUrlNotSet_shouldKeepTheRequestAndResponse() -> None:
    raw = serializer.serialize(
        "v3.capture.request_response",
        {
            "request": {"method": "GET", "url": "https://ostorlab.co/robots.txt"},
            "response": {"url": "https://ostorlab.co/robots.txt", "status": 200},
        },
    ).SerializeToString()

    message = serializer.deserialize("v3.capture.request_response", raw)

    assert isinstance(message, request_response_pb2.Message)
    assert message.HasField("page_url") is False
    assert message.request.url == "https://ostorlab.co/robots.txt"
    assert message.response.status == 200
