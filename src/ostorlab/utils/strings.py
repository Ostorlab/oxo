"""Utils to generate and manipulate strings."""

import json
import random
import re
import string
from typing import Any

REDACTED = "<redacted>"

# Matches keys whose last word is a secret, e.g. `password`, `session_token`,
# `device_relay_credentials`, `apiKey` or `password2`, but not `token_count` or
# `password_policy`.
_SENSITIVE_KEY_PATTERN = re.compile(
    r"(?:^|_)(?:passwords?|passwd|secrets?|tokens?|api_?keys?|private_?keys?"
    r"|(?:secret|session|signing|encryption)_?(?:access_?)?keys?|session_?ids?"
    r"|credentials?|authorization|cookies?)"
    r"[0-9]*$",
    re.IGNORECASE,
)
# Normalizes key word separators to `_`, e.g. `X-Auth-Token` to `X_Auth_Token`.
_KEY_SEPARATOR_PATTERN = re.compile(r"[\s\-.]+")
# Splits camelCase words, including acronyms, e.g. `AWSPrivateKey` to `AWS_Private_Key`.
_CAMEL_CASE_BOUNDARY_PATTERN = re.compile(
    r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])"
)
# Matches URL query and fragment parameters, e.g. `&X-Goog-Signature=...`, capturing
# their name and value.
_URL_QUERY_PARAM_PATTERN = re.compile(r"([?&#]([^=?&#\s\"']+)=)([^&#\s\"']*)")
# Matches signature query parameter names of signed URLs, e.g. `X-Amz-Signature`.
_URL_SIGNATURE_PARAM_PATTERN = re.compile(
    r"(?:^|[_\-.])(?:signature|sig)$", re.IGNORECASE
)
# Maps the name key of name/value pairs to their value keys.
_NAME_VALUE_KEYS = {
    "arg_name": ("arg_value", "arg_value_bytes"),
    "name": ("value", "value_bytes"),
    "key": ("value", "value_bytes"),
}
# Matches the password of URL user info, e.g. `https://user:password@host`.
_URL_USER_INFO_PASSWORD_PATTERN = re.compile(r"(://[^/?#\s:@]*:)[^/?#\s@]+@")


def random_string(length: int, alphabet: str = string.ascii_lowercase) -> str:
    """Generates a random string of a specified length.

    Args:
        length: Length of the string to generate.
        alphabet: The alphabet used to generate the random string, defaults to ascii lower case.

    Returns:
        Randomly generated string.
    """
    if length <= 0:
        raise ValueError(f"Invalid string length: {length}")

    result = "".join(random.choice(alphabet) for _ in range(length))
    return result


def _is_sensitive_key(key: Any) -> bool:
    """Check if a key name designates a secret value, like a password or a token."""
    if isinstance(key, bytes):
        key = key.decode(errors="ignore")
    if isinstance(key, str) is False:
        return False
    key = _CAMEL_CASE_BOUNDARY_PATTERN.sub("_", key)
    key = _KEY_SEPARATOR_PATTERN.sub("_", key)
    return _SENSITIVE_KEY_PATTERN.search(key) is not None


def _redact_url_query_param(match: re.Match[str]) -> str:
    """Redact the value of a URL query parameter if its name is sensitive.

    Values of other parameters are redacted recursively, as they may be nested URLs.
    """
    name = match.group(2)
    if (
        _is_sensitive_key(name) is True
        or _URL_SIGNATURE_PARAM_PATTERN.search(name) is not None
    ):
        return f"{match.group(1)}{REDACTED}"
    value = _URL_QUERY_PARAM_PATTERN.sub(_redact_url_query_param, match.group(3))
    return f"{match.group(1)}{value}"


def _format_dict_data(data: dict[Any, Any]) -> dict[Any, Any]:
    # Name/value pairs, e.g. `{"arg_name": "token", "arg_value": [...]}` for args or
    # `{"name": "Authorization", "value": "..."}` for headers, have their values
    # redacted when the name is sensitive.
    sensitive_value_keys = {
        value_key
        for name_key, value_keys in _NAME_VALUE_KEYS.items()
        if _is_sensitive_key(data.get(name_key)) is True
        for value_key in value_keys
    }
    formatted: dict[Any, Any] = {}
    for key, value in data.items():
        if _is_sensitive_key(key) is True or (key in sensitive_value_keys):
            formatted[key] = REDACTED
        else:
            formatted[key] = _format_data(value)
    return formatted


def _format_data(data: Any) -> Any:
    if isinstance(data, dict):
        return _format_dict_data(data)
    elif isinstance(data, list):
        return [_format_data(v) for v in data]
    elif isinstance(data, bytes):
        return f"<bytes of length {len(data)}>"
    elif isinstance(data, str):
        data = _URL_QUERY_PARAM_PATTERN.sub(_redact_url_query_param, data)
        data = _URL_USER_INFO_PASSWORD_PATTERN.sub(rf"\1{REDACTED}@", data)
        if len(data) > 4096:
            return f"{data[:256]}... <string of length {len(data)}>"
        else:
            return data
    else:
        return data


def format_dict(dict_obj: dict[str, Any]) -> str:
    """Format message for logging, filtering out large values and redacting secrets.

    Values of keys that look sensitive (passwords, tokens, credentials...) and signature
    parameters of signed URLs are replaced with a `<redacted>` placeholder.
    """
    filtered_data = _format_data(dict_obj)
    return json.dumps(filtered_data, indent=2)
