from ostorlab.agent.message.proto.v3.fingerprint.store.ios.listing import listing_pb2


def testMessage_whenCreateWithValidData_shouldSerializeAndDeserializeCorrectly() -> (
    None
):
    msg = listing_pb2.Message()
    msg.bundle_id = "com.example.app"
    msg.name = "Example App"
    msg.icon_url = "https://is1-ssl.mzstatic.com/image/icon.png"
    msg.category = "Utilities"
    msg.rating = 4.7
    msg.rating_count = 35000
    msg.release_date = "2009-05-04T02:43:49Z"
    msg.last_update_date = "2026-10-26T12:28:55Z"
    msg.version = "3.2.1"
    msg.price = 2.99
    msg.currency = "USD"
    msg.content_rating = "4+"
    msg.description = "An example application."
    msg.screenshot_urls.extend(
        [
            "https://is1-ssl.mzstatic.com/image/screenshot1.png",
            "https://is1-ssl.mzstatic.com/image/screenshot2.png",
        ]
    )
    msg.store_url = "https://apps.apple.com/us/app/example-app/id123456789"

    serialized = msg.SerializeToString()
    deserialized_msg = listing_pb2.Message()
    deserialized_msg.ParseFromString(serialized)

    assert deserialized_msg.bundle_id == "com.example.app"
    assert deserialized_msg.name == "Example App"
    assert deserialized_msg.icon_url == "https://is1-ssl.mzstatic.com/image/icon.png"
    assert deserialized_msg.category == "Utilities"
    assert deserialized_msg.rating == 4.7
    assert deserialized_msg.rating_count == 35000
    assert deserialized_msg.release_date == "2009-05-04T02:43:49Z"
    assert deserialized_msg.last_update_date == "2026-10-26T12:28:55Z"
    assert deserialized_msg.version == "3.2.1"
    assert deserialized_msg.price == 2.99
    assert deserialized_msg.currency == "USD"
    assert deserialized_msg.content_rating == "4+"
    assert deserialized_msg.description == "An example application."
    assert list(deserialized_msg.screenshot_urls) == [
        "https://is1-ssl.mzstatic.com/image/screenshot1.png",
        "https://is1-ssl.mzstatic.com/image/screenshot2.png",
    ]
    assert (
        deserialized_msg.store_url
        == "https://apps.apple.com/us/app/example-app/id123456789"
    )


def testMessage_whenCreateEmpty_shouldHaveDefaultValues() -> None:
    msg = listing_pb2.Message()

    assert msg.bundle_id == ""
    assert msg.name == ""
    assert msg.rating == 0.0
    assert msg.rating_count == 0
    assert msg.HasField("price") is False
    assert len(msg.screenshot_urls) == 0


def testMessage_whenSerializeEmpty_shouldDeserializeToEmpty() -> None:
    msg = listing_pb2.Message()

    serialized = msg.SerializeToString()
    deserialized_msg = listing_pb2.Message()
    deserialized_msg.ParseFromString(serialized)

    assert deserialized_msg.bundle_id == ""
    assert len(deserialized_msg.screenshot_urls) == 0
