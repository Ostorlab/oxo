from ostorlab.agent.message.proto.v3.fingerprint.store.android.listing import (
    listing_pb2,
)


def testMessage_whenCreateWithValidData_shouldSerializeAndDeserializeCorrectly() -> (
    None
):
    msg = listing_pb2.Message()
    msg.package_name = "com.example.app"
    msg.name = "Example App"
    msg.icon_url = "https://play-lh.googleusercontent.com/icon"
    msg.category = "Tools"
    msg.rating = 4.5
    msg.rating_count = 120000
    msg.installs = "10,000,000+"
    msg.release_date = "2010-10-18"
    msg.last_update_date = "2026-10-26T12:28:55Z"
    msg.version = "3.2.1"
    msg.price = 0.0
    msg.currency = "USD"
    msg.has_in_app_purchases = True
    msg.content_rating = "Everyone"
    msg.description = "An example application."
    msg.screenshot_urls.extend(
        [
            "https://play-lh.googleusercontent.com/screenshot1",
            "https://play-lh.googleusercontent.com/screenshot2",
        ]
    )
    msg.privacy_policy_url = "https://example.com/privacy"
    msg.store_url = "https://play.google.com/store/apps/details?id=com.example.app"

    serialized = msg.SerializeToString()
    deserialized_msg = listing_pb2.Message()
    deserialized_msg.ParseFromString(serialized)

    assert deserialized_msg.package_name == "com.example.app"
    assert deserialized_msg.name == "Example App"
    assert deserialized_msg.icon_url == "https://play-lh.googleusercontent.com/icon"
    assert deserialized_msg.category == "Tools"
    assert deserialized_msg.rating == 4.5
    assert deserialized_msg.rating_count == 120000
    assert deserialized_msg.installs == "10,000,000+"
    assert deserialized_msg.release_date == "2010-10-18"
    assert deserialized_msg.last_update_date == "2026-10-26T12:28:55Z"
    assert deserialized_msg.version == "3.2.1"
    assert deserialized_msg.HasField("price") is True
    assert deserialized_msg.price == 0.0
    assert deserialized_msg.currency == "USD"
    assert deserialized_msg.has_in_app_purchases is True
    assert deserialized_msg.content_rating == "Everyone"
    assert deserialized_msg.description == "An example application."
    assert list(deserialized_msg.screenshot_urls) == [
        "https://play-lh.googleusercontent.com/screenshot1",
        "https://play-lh.googleusercontent.com/screenshot2",
    ]
    assert deserialized_msg.privacy_policy_url == "https://example.com/privacy"
    assert (
        deserialized_msg.store_url
        == "https://play.google.com/store/apps/details?id=com.example.app"
    )


def testMessage_whenCreateEmpty_shouldHaveDefaultValues() -> None:
    msg = listing_pb2.Message()

    assert msg.package_name == ""
    assert msg.name == ""
    assert msg.rating == 0.0
    assert msg.rating_count == 0
    assert msg.installs == ""
    assert msg.has_in_app_purchases is False
    assert msg.HasField("price") is False
    assert len(msg.screenshot_urls) == 0


def testMessage_whenSerializeEmpty_shouldDeserializeToEmpty() -> None:
    msg = listing_pb2.Message()

    serialized = msg.SerializeToString()
    deserialized_msg = listing_pb2.Message()
    deserialized_msg.ParseFromString(serialized)

    assert deserialized_msg.package_name == ""
    assert deserialized_msg.HasField("has_in_app_purchases") is False
    assert len(deserialized_msg.screenshot_urls) == 0
