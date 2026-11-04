from ostorlab.agent.message.proto.v3.asset.store.android_store import android_store_pb2


def testMessage_whenCreateWithListingData_shouldSerializeAndDeserializeCorrectly() -> (
    None
):
    message = android_store_pb2.Message(
        package_name="com.example.app",
        name="Example App",
        icon_url="https://play-lh.googleusercontent.com/icon",
        category="Communication",
        rating=4.5,
        rating_count=120000,
        installs="10,000,000+",
        release_date="2010-10-18",
        last_update_date="2026-10-26T12:28:55Z",
        version="3.2.1",
        price=0.99,
        currency="USD",
        has_in_app_purchases=True,
        content_rating="Everyone",
        description="An example app.",
        screenshot_urls=[
            "https://play-lh.googleusercontent.com/screenshot1",
            "https://play-lh.googleusercontent.com/screenshot2",
        ],
        privacy_policy_url="https://example.com/privacy",
        store_url="https://play.google.com/store/apps/details?id=com.example.app",
    )

    deserialized = android_store_pb2.Message()
    deserialized.ParseFromString(message.SerializeToString())

    assert deserialized == message
    assert deserialized.package_name == "com.example.app"
    assert deserialized.rating == 4.5
    assert deserialized.rating_count == 120000
    assert deserialized.installs == "10,000,000+"
    assert deserialized.price == 0.99
    assert deserialized.has_in_app_purchases is True
    assert list(deserialized.screenshot_urls) == [
        "https://play-lh.googleusercontent.com/screenshot1",
        "https://play-lh.googleusercontent.com/screenshot2",
    ]


def testMessage_whenCreateWithPackageNameOnly_shouldLeaveListingFieldsUnset() -> None:
    message = android_store_pb2.Message(package_name="com.example.app")

    deserialized = android_store_pb2.Message()
    deserialized.ParseFromString(message.SerializeToString())

    assert deserialized.package_name == "com.example.app"
    assert deserialized.HasField("name") is False
    assert deserialized.HasField("rating") is False
    assert deserialized.HasField("has_in_app_purchases") is False
    assert list(deserialized.screenshot_urls) == []


def testMessage_whenCreateEmpty_shouldHaveDefaultValues() -> None:
    message = android_store_pb2.Message()

    assert message.package_name == ""
    assert message.name == ""
    assert message.rating == 0.0
    assert message.rating_count == 0
    assert message.price == 0.0
    assert message.has_in_app_purchases is False
    assert list(message.screenshot_urls) == []


def testMessage_whenSerializeEmpty_shouldDeserializeToEmpty() -> None:
    message = android_store_pb2.Message()

    serialized = message.SerializeToString()
    deserialized = android_store_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert serialized == b""
    assert deserialized == android_store_pb2.Message()
