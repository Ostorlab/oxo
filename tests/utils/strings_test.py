"""Unit test for strings utils module."""

import pytest

from ostorlab.utils import strings


# pylint: disable=W0631
def testRandomString_whenLengthIsValid_returnsARandomStringOfSpecifiedSize():
    """Tests if a proper random string is generated."""
    generated = strings.random_string(6)

    assert isinstance(generated, str)
    assert len(generated) == 6


def testRandomString_whenLengthIsInvalid_raisesAnException():
    """Tests if an exception is raised when a incorrect length value is provided."""
    with pytest.raises(ValueError):
        strings.random_string(0)


def testToString_whenDictHasLongString_returnsTruncatedString():
    """Tests if a long string is truncated."""
    long_string = "a" * 5000
    data = {"a": long_string}
    result = strings.format_dict(data)
    assert f'"{long_string[:256]}... <string of length {len(long_string)}>"' in result


def testToString_whenDictHasShortString_returnsFullString():
    """Tests if a short string is not truncated."""
    short_string = "a" * 100
    data = {"a": short_string}
    result = strings.format_dict(data)
    assert f'"{short_string}"' in result
    assert "<string of length" not in result


def testToString_whenDictHasBytes_returnsBytesPlaceholder():
    """Tests if bytes are replaced with a placeholder."""
    data = {"a": b"test"}
    result = strings.format_dict(data)
    assert '"<bytes of length 4>"' in result


def testToString_whenDictIsNested_returnsFilteredString():
    """Tests if nested dict is filtered."""
    long_string = "a" * 5000
    data = {"a": {"b": long_string}}
    result = strings.format_dict(data)
    assert f'"{long_string[:256]}... <string of length {len(long_string)}>"' in result


def testToString_whenDictHasList_returnsFilteredString():
    """Tests if list elements are filtered."""
    long_string = "a" * 5000
    data = {"a": [long_string, b"test"]}
    result = strings.format_dict(data)
    assert f'"{long_string[:256]}... <string of length {len(long_string)}>"' in result
    assert '"<bytes of length 4>"' in result


def testToString_whenObjectIsNotStringOrBytes_returnsObject():
    """Tests if an object that is not a string or bytes is returned as is."""
    data = {"a": 123, "b": True, "c": None}
    result = strings.format_dict(data)
    assert '"a": 123' in result
    assert '"b": true' in result
    assert '"c": null' in result


@pytest.mark.parametrize(
    "key",
    [
        "password",
        "passwd",
        "secret",
        "client_secret",
        "token",
        "session_token",
        "device_session_token",
        "sessionToken",
        "X-Auth-Token",
        "api_key",
        "apikey",
        "apiKey",
        "AWSPrivateKey",
        "AWSSecret",
        "HTTPAuthorization",
        "private_key",
        "session_key",
        "sessionKey",
        "signing_key",
        "encryption_key",
        "password1",
        "token2",
        "api_key1",
        "session_id",
        "sessionid",
        "api-key",
        "private-key",
        "secret-key",
        "auth.token",
        "Session Token",
        "secret_key",
        "secretKey",
        "aws_secret_access_key",
        "credentials",
        "device_relay_credentials",
        "Authorization",
        "cookie",
    ],
)
def testFormatDict_whenKeyIsSensitive_redactsValue(key: str) -> None:
    """Tests if values of sensitive keys are redacted."""
    data = {key: "fake-secret-value", "name": "visible"}

    result = strings.format_dict(data)

    assert "fake-secret-value" not in result
    assert f'"{key}": "<redacted>"' in result
    assert '"name": "visible"' in result


@pytest.mark.parametrize(
    "key",
    [
        "token_count",
        "session_count",
        "tokenizer",
        "password_policy",
        "keyboard",
        "public_key",
        "AWSPublicKey",
        "name",
    ],
)
def testFormatDict_whenKeyIsNotSensitive_keepsValue(key: str) -> None:
    """Tests if values of keys that only contain a sensitive word are not redacted."""
    data = {key: "visible-value"}

    result = strings.format_dict(data)

    assert f'"{key}": "visible-value"' in result
    assert "<redacted>" not in result


def testFormatDict_whenSensitiveKeyHasNestedDict_redactsWholeSubtree() -> None:
    """Tests if a sensitive key holding a dict is redacted entirely."""
    data = {
        "device_relay_credentials": {
            "login_password": {"username": "fake-user", "password": "fake-password"}
        }
    }

    result = strings.format_dict(data)

    assert "fake-user" not in result
    assert "fake-password" not in result
    assert '"device_relay_credentials": "<redacted>"' in result


def testFormatDict_whenArgNameIsSensitive_redactsArgValues() -> None:
    """Tests if the values of a name/value argument pair with a sensitive name are redacted."""
    data = {
        "args": [
            {
                "arg_name": "session_token",
                "arg_value": ["fake-session-token"],
                "arg_value_bytes": [b"fake-session-token"],
            },
            {"arg_name": "target", "arg_value": ["com.example.app"]},
        ]
    }

    result = strings.format_dict(data)

    assert "fake-session-token" not in result
    assert '"arg_name": "session_token"' in result
    assert '"arg_value": "<redacted>"' in result
    assert '"arg_value_bytes": "<redacted>"' in result
    assert '"com.example.app"' in result


@pytest.mark.parametrize(
    "url",
    [
        (
            "https://storage.googleapis.com/bucket/app.ipa?X-Goog-Algorithm=GOOG4-RSA-SHA256"
            "&X-Goog-Credential=fake-credential&X-Goog-Expires=600&X-Goog-Signature=fakesig"
        ),
        (
            "https://bucket.s3.amazonaws.com/app.ipa?X-Amz-Credential=fake-credential"
            "&X-Amz-Security-Token=fake-token&X-Amz-Signature=fakesig"
        ),
        (
            "https://example.com/app.ipa?Signature=fakesig&sig=fakesig&token=fake-token"
            "&access_token=fake-token"
        ),
        "https://api.example.com/v1/resource?api_key=fake-token&apikey=fake-token",
        (
            "https://example.com/callback?id_token=fake-token&refresh_token=fake-token"
            "&auth_token=fake-token&accessToken=fake-token&idToken=fake-token"
            "&refreshToken=fake-token"
        ),
    ],
)
def testFormatDict_whenStringHasSignedUrl_redactsSignatureParameters(
    url: str,
) -> None:
    """Tests if signature, credential and token query parameters of URLs are redacted."""
    data = {"app_url": url}

    result = strings.format_dict(data)

    assert "fake-credential" not in result
    assert "fake-token" not in result
    assert "fakesig" not in result
    assert "<redacted>" in result


def testFormatDict_whenStringHasSignedUrl_keepsOtherParameters() -> None:
    """Tests if non sensitive query parameters of signed URLs are kept."""
    data = {
        "app_url": "https://storage.googleapis.com/bucket/app.ipa"
        "?X-Goog-Expires=600&X-Goog-Signature=fakesig&X-Goog-SignedHeaders=host"
    }

    result = strings.format_dict(data)

    assert (
        "https://storage.googleapis.com/bucket/app.ipa?X-Goog-Expires=600"
        "&X-Goog-Signature=<redacted>&X-Goog-SignedHeaders=host"
    ) in result


def testFormatDict_whenMessageIsUseDevice_redactsAllSecrets() -> None:
    """Tests if a v3.use.device message is logged without any of its secrets."""
    data = {
        "device_id": "fake-device-id",
        "device_type": "iPhone",
        "device_relay": {"name": "relay", "address": "10.0.0.1", "port": 22},
        "device_relay_credentials": {
            "login_password": {"username": "root", "password": "fake-relay-password"}
        },
        "device_session_token": "fake-device-session-token",
        "args": [
            {"arg_name": "session_token", "arg_value": ["fake-arg-session-token"]},
            {
                "arg_name": "app_url",
                "arg_value": [
                    (
                        "https://storage.googleapis.com/bucket/app.ipa"
                        "?X-Goog-Credential=fake-goog-credential"
                        "&X-Goog-Signature=fake-goog-signature"
                    )
                ],
            },
        ],
        "app_url": "https://storage.googleapis.com/bucket/app.ipa"
        "?X-Goog-Credential=fake-goog-credential&X-Goog-Signature=fake-goog-signature",
    }

    result = strings.format_dict(data)

    assert "fake-relay-password" not in result
    assert "fake-device-session-token" not in result
    assert "fake-arg-session-token" not in result
    assert "fake-goog-credential" not in result
    assert "fake-goog-signature" not in result
    assert '"device_id": "fake-device-id"' in result
    assert '"address": "10.0.0.1"' in result
    assert "https://storage.googleapis.com/bucket/app.ipa" in result


def testFormatDict_whenStringHasUrlWithUserInfoPassword_redactsPassword() -> None:
    """Tests if the password of a URL user info is redacted."""
    data = {"relay": "ssh://fake-user:fake-password@relay.example.com:22/path"}

    result = strings.format_dict(data)

    assert "fake-password" not in result
    assert '"ssh://fake-user:<redacted>@relay.example.com:22/path"' in result


def testFormatDict_whenStringHasUrlWithPort_keepsUrl() -> None:
    """Tests if a URL with a port and no user info is not altered."""
    data = {"url": "https://example.com:8443/path?q=1"}

    result = strings.format_dict(data)

    assert '"url": "https://example.com:8443/path?q=1"' in result


def testFormatDict_whenNameValuePairHasSensitiveName_redactsValue() -> None:
    """Tests if values of name/value pairs, like headers or form inputs, are redacted."""
    data = {
        "url": "https://example.com/login",
        "extra_headers": [
            {"name": "Authorization", "value": "Bearer fake-bearer-token"},
            {"name": "Accept", "value": "application/json"},
        ],
        "form": {
            "inputs": [
                {"name": "password", "type": "password", "value": "fake-password"},
                {"name": "username", "type": "text", "value": "fake-user"},
            ]
        },
    }

    result = strings.format_dict(data)

    assert "fake-bearer-token" not in result
    assert "fake-password" not in result
    assert '"name": "Authorization"' in result
    assert '"value": "application/json"' in result
    assert '"value": "fake-user"' in result
    assert '"type": "password"' in result


def testFormatDict_whenStringHasUrlWithEmptyUserAndPassword_redactsPassword() -> None:
    """Tests if the password of a URL user info with an empty username is redacted."""
    data = {"relay": "ssh://:fake-password@relay.example.com"}

    result = strings.format_dict(data)

    assert "fake-password" not in result
    assert '"ssh://:<redacted>@relay.example.com"' in result


def testFormatDict_whenKeyValuePairHasSensitiveKey_redactsValue() -> None:
    """Tests if values of key/value pairs, like local storage items, are redacted."""
    data = {
        "localstorage_items": [
            {
                "url": "https://example.com",
                "key": "access_token",
                "value": "fake-token",
            },
            {"url": "https://example.com", "key": "theme", "value": "dark"},
        ]
    }

    result = strings.format_dict(data)

    assert "fake-token" not in result
    assert '"key": "access_token"' in result
    assert '"value": "dark"' in result


def testFormatDict_whenUrlHasPortAndQueryValueWithAt_keepsUrl() -> None:
    """Tests if a URL with a port and an `@` in its query is not taken for user info."""
    data = {"url": "https://example.com:8443?next=user@example.com"}

    result = strings.format_dict(data)

    assert '"url": "https://example.com:8443?next=user@example.com"' in result


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/callback#access_token=fake-token&state=1",
        "https://example.com/redirect?next=https://example.com/cb?access_token=fake-token&x=1",
    ],
)
def testFormatDict_whenUrlHasTokenInFragmentOrNestedUrl_redactsToken(url: str) -> None:
    """Tests if tokens in URL fragments and in URLs nested in parameters are redacted."""
    data = {"url": url}

    result = strings.format_dict(data)

    assert "fake-token" not in result
    assert "access_token=<redacted>" in result


def testFormatDict_whenNameIsSensitive_keepsOtherValueLikeKeys() -> None:
    """Tests if only the value keys of a sensitive name/value pair are redacted."""
    data = {"name": "password", "value": "fake-password", "value_type": "string"}

    result = strings.format_dict(data)

    assert "fake-password" not in result
    assert '"value_type": "string"' in result


def testFormatDict_whenSensitiveParamValueIsUrl_redactsWholeValue() -> None:
    """Tests if a sensitive parameter whose value is a URL is redacted entirely."""
    data = {
        "url": "https://example.com/redirect?token=https://example.com/cb?x=fake-x&y=1"
    }

    result = strings.format_dict(data)

    assert "fake-x" not in result
    assert '"https://example.com/redirect?token=<redacted>&y=1"' in result
