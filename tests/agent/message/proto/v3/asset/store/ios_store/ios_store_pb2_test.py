from ostorlab.agent.message.proto.v3.asset.store.ios_store import ios_store_pb2


def testMessage_whenCreateWithListingData_shouldSerializeAndDeserializeCorrectly() -> (
    None
):
    message = ios_store_pb2.Message(
        bundle_id="com.example.app",
        name="Example App",
        icon_url="https://is1-ssl.mzstatic.com/image/icon.png",
        category="Social Networking",
        rating=4.7,
        rating_count=35000,
        release_date="2009-05-04T02:43:49Z",
        last_update_date="2026-10-26T12:28:55Z",
        version="3.2.1",
        price=2.99,
        currency="USD",
        content_rating="12+",
        description="An example app.",
        screenshot_urls=["https://is1-ssl.mzstatic.com/image/screenshot1.png"],
        store_url="https://apps.apple.com/us/app/example/id123",
    )

    deserialized = ios_store_pb2.Message()
    deserialized.ParseFromString(message.SerializeToString())

    assert deserialized == message
    assert deserialized.bundle_id == "com.example.app"
    assert deserialized.rating == 4.7
    assert deserialized.rating_count == 35000
    assert deserialized.price == 2.99
    assert list(deserialized.screenshot_urls) == [
        "https://is1-ssl.mzstatic.com/image/screenshot1.png"
    ]


def testMessage_whenCreateWithBundleIdOnly_shouldLeaveListingFieldsUnset() -> None:
    message = ios_store_pb2.Message(bundle_id="com.example.app")

    deserialized = ios_store_pb2.Message()
    deserialized.ParseFromString(message.SerializeToString())

    assert deserialized.bundle_id == "com.example.app"
    assert deserialized.HasField("name") is False
    assert deserialized.HasField("rating") is False
    assert list(deserialized.screenshot_urls) == []


def testMessage_whenCreateEmpty_shouldHaveDefaultValues() -> None:
    message = ios_store_pb2.Message()

    assert message.bundle_id == ""
    assert message.name == ""
    assert message.rating == 0.0
    assert message.rating_count == 0
    assert message.price == 0.0
    assert list(message.screenshot_urls) == []


def testMessage_whenSerializeEmpty_shouldDeserializeToEmpty() -> None:
    message = ios_store_pb2.Message()

    serialized = message.SerializeToString()
    deserialized = ios_store_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert serialized == b""
    assert deserialized == ios_store_pb2.Message()
