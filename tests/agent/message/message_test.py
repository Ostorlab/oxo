"""Tests for message module."""

from ostorlab.agent.message import message


def testMessageSerializeDeserialize_whenSelectorIsValid_generatesProperProto() -> None:
    """Test message proper serialization from a dict object to a protobuf based on the selector."""
    serialized = message.Message.from_data(
        "v3.fingerprint.file",
        {
            "path": "/etc/hosts",
        },
    )
    deserialized = message.Message.from_raw("v3.fingerprint.file", serialized.raw)

    assert isinstance(serialized.raw, bytes)
    assert deserialized.data.get("path") == "/etc/hosts"


def testMessageSerializeDeserializeWithEnum_whenSelectorIsValid_generatesProperProto() -> (
    None
):
    """Test message proper serialization with enum from a dict object to a protobuf based on the selector."""
    serialized = message.Message.from_data(
        "v3.report.vulnerability",
        {
            "title": "some_title",
            "technical_detail": "some_details",
            "risk_rating": "MEDIUM",
        },
    )
    deserialized = message.Message.from_raw("v3.report.vulnerability", serialized.raw)

    assert isinstance(serialized.raw, bytes)
    assert deserialized.data.get("risk_rating") == "MEDIUM"


def testMessageSerializeDeserializeForBytes_whenSelectorIsValid_generatesProperProto() -> (
    None
):
    """Test message proper serialization from a dict object to a protobuf based on the selector."""
    serialized = message.Message.from_data(
        "v3.asset.file",
        {
            "content": b"test",
        },
    )
    deserialized = message.Message.from_raw("v3.asset.file", serialized.raw)

    assert isinstance(serialized.raw, bytes)
    assert deserialized.data.get("content") == b"test"


def testMessageSerializeDeserialize_Forv3CaptureFilesystem_generatesProperProto() -> (
    None
):
    """Test message proper serialization from a dict object to a protobuf based on the selector."""
    serialized = message.Message.from_data(
        "v3.capture.filesystem",
        {
            "event": "ACCESS",
            "filename": "/etc/hosts",
            "pid": 1,
            "gid": 1,
            "mode": 600,
            "ppid": 1,
            "proc": "init",
        },
    )
    deserialized = message.Message.from_raw("v3.capture.filesystem", serialized.raw)

    assert isinstance(serialized.raw, bytes)
    assert deserialized.data.get("event") == "ACCESS"
    assert deserialized.data.get("filename") == "/etc/hosts"


def testMessageSerializeDeserialize_Forv3CaptureTcp_generatesProperProto() -> None:
    """Test serialization/deserialization of a raw TCP message (v3.capture.tcp)."""
    serialized = message.Message.from_data(
        "v3.capture.tcp",
        {
            "id": "flow-1",
            "seq": 2,
            "from_client": True,
            "server_host": "1.2.3.4",
            "server_port": 443,
            "client_host": "10.0.0.1",
            "client_port": 51515,
            "sni": "example.com",
            "tls": True,
            "content": b"\x16\x03hello",
            "timestamp": 1.0,
        },
    )
    deserialized = message.Message.from_raw("v3.capture.tcp", serialized.raw)

    assert isinstance(serialized.raw, bytes)
    assert deserialized.data.get("id") == "flow-1"
    assert deserialized.data.get("seq") == 2
    assert deserialized.data.get("from_client") is True
    assert deserialized.data.get("server_host") == "1.2.3.4"
    assert deserialized.data.get("content") == b"\x16\x03hello"


def testMessageSerializeDeserialize_Forv3FingerprintStoreAndroid_generatesProperProto() -> (
    None
):
    """Test serialization/deserialization of a Google Play store listing (v3.fingerprint.store.android)."""
    serialized = message.Message.from_data(
        "v3.fingerprint.store.android",
        {
            "package_name": "com.example.app",
            "name": "Example App",
            "rating": 4.5,
            "rating_count": 120000,
            "installs": "10,000,000+",
            "version": "3.2.1",
            "price": 0.99,
            "currency": "USD",
            "has_in_app_purchases": True,
            "screenshot_urls": ["https://play-lh.googleusercontent.com/screenshot1"],
            "privacy_policy_url": "https://example.com/privacy",
            "store_url": "https://play.google.com/store/apps/details?id=com.example.app",
        },
    )
    deserialized = message.Message.from_raw(
        "v3.fingerprint.store.android", serialized.raw
    )

    assert isinstance(serialized.raw, bytes)
    assert deserialized.data.get("package_name") == "com.example.app"
    assert deserialized.data.get("name") == "Example App"
    assert deserialized.data.get("rating") == 4.5
    assert deserialized.data.get("rating_count") == 120000
    assert deserialized.data.get("installs") == "10,000,000+"
    assert deserialized.data.get("version") == "3.2.1"
    assert deserialized.data.get("price") == 0.99
    assert deserialized.data.get("currency") == "USD"
    assert deserialized.data.get("has_in_app_purchases") is True
    assert deserialized.data.get("screenshot_urls") == [
        "https://play-lh.googleusercontent.com/screenshot1"
    ]
    assert deserialized.data.get("privacy_policy_url") == "https://example.com/privacy"
    assert (
        deserialized.data.get("store_url")
        == "https://play.google.com/store/apps/details?id=com.example.app"
    )


def testMessageSerializeDeserialize_Forv3FingerprintStoreIos_generatesProperProto() -> (
    None
):
    """Test serialization/deserialization of an App Store listing (v3.fingerprint.store.ios)."""
    serialized = message.Message.from_data(
        "v3.fingerprint.store.ios",
        {
            "bundle_id": "com.example.app",
            "name": "Example App",
            "rating": 4.7,
            "rating_count": 35000,
            "version": "3.2.1",
            "price": 2.99,
            "currency": "USD",
            "screenshot_urls": ["https://is1-ssl.mzstatic.com/image/screenshot1.png"],
            "store_url": "https://apps.apple.com/us/app/example-app/id123456789",
        },
    )
    deserialized = message.Message.from_raw("v3.fingerprint.store.ios", serialized.raw)

    assert isinstance(serialized.raw, bytes)
    assert deserialized.data.get("bundle_id") == "com.example.app"
    assert deserialized.data.get("name") == "Example App"
    assert deserialized.data.get("rating") == 4.7
    assert deserialized.data.get("rating_count") == 35000
    assert deserialized.data.get("version") == "3.2.1"
    assert deserialized.data.get("price") == 2.99
    assert deserialized.data.get("currency") == "USD"
    assert deserialized.data.get("screenshot_urls") == [
        "https://is1-ssl.mzstatic.com/image/screenshot1.png"
    ]
    assert (
        deserialized.data.get("store_url")
        == "https://apps.apple.com/us/app/example-app/id123456789"
    )


def testMessageSerializeDeserialize_Forv3FingerprintStoreAndroidWithPrivacyData_generatesProperProto() -> (
    None
):
    """Test serialization/deserialization of a Google Play store listing with its data safety section (v3.fingerprint.store.android)."""
    data = {
        "package_name": "com.example.app",
        "name": "Example App",
        "icon_url": "https://play-lh.googleusercontent.com/icon",
        "category": "Communication",
        "rating": 4.5,
        "rating_count": 120000,
        "installs": "10,000,000+",
        "release_date": "2010-10-18",
        "last_update_date": "2026-10-26T12:28:55Z",
        "version": "3.2.1",
        "price": 0.99,
        "currency": "USD",
        "has_in_app_purchases": True,
        "content_rating": "Everyone",
        "description": "An example app.",
        "screenshot_urls": ["https://play-lh.googleusercontent.com/screenshot1"],
        "privacy_policy_url": "https://example.com/privacy",
        "store_url": "https://play.google.com/store/apps/details?id=com.example.app",
        "data_safety": {
            "url": "https://play.google.com/store/apps/datasafety?id=com.example.app&hl=en",
            "data_shared": [
                {
                    "category": "Device or other IDs",
                    "data_type": "Device or other IDs",
                    "is_optional": False,
                    "purposes": ["Advertising or marketing"],
                }
            ],
            "data_collected": [
                {
                    "category": "Location",
                    "data_type": "Approximate location",
                    "is_optional": True,
                    "purposes": ["App functionality", "Analytics"],
                }
            ],
            "security_practices": ["Data is encrypted in transit"],
        },
    }

    serialized = message.Message.from_data("v3.fingerprint.store.android", data)
    deserialized = message.Message.from_raw(
        "v3.fingerprint.store.android", serialized.raw
    )

    assert isinstance(serialized.raw, bytes)
    assert deserialized.data == data


def testMessageSerializeDeserialize_Forv3FingerprintStoreIosWithPrivacyData_generatesProperProto() -> (
    None
):
    """Test serialization/deserialization of an App Store listing with its privacy policy URL and privacy labels (v3.fingerprint.store.ios)."""
    location = {
        "identifier": "LOCATION",
        "name": "Location",
        "data_types": ["Precise Location"],
    }
    data = {
        "bundle_id": "com.example.app",
        "name": "Example App",
        "icon_url": "https://is1-ssl.mzstatic.com/icon.png",
        "category": "Social Networking",
        "rating": 4.7,
        "rating_count": 13000000,
        "release_date": "2009-05-04T02:43:49Z",
        "last_update_date": "2026-10-26T12:28:55Z",
        "version": "26.10.1",
        "price": 0.0,
        "currency": "USD",
        "content_rating": "12+",
        "description": "An example app.",
        "screenshot_urls": ["https://is1-ssl.mzstatic.com/screenshot1.png"],
        "store_url": "https://apps.apple.com/us/app/example/id310633997",
        "privacy_policy_url": "https://example.com/privacy",
        "privacy_labels": [
            {
                "identifier": "DATA_USED_TO_TRACK_YOU",
                "name": "Data Used to Track You",
                "categories": [location],
            },
            {
                "identifier": "DATA_LINKED_TO_YOU",
                "name": "Data Linked to You",
                "purposes": [
                    {
                        "identifier": "ANALYTICS",
                        "name": "Analytics",
                        "categories": [location],
                    }
                ],
            },
        ],
    }

    serialized = message.Message.from_data("v3.fingerprint.store.ios", data)
    deserialized = message.Message.from_raw("v3.fingerprint.store.ios", serialized.raw)

    assert isinstance(serialized.raw, bytes)
    assert deserialized.data == data
