"""Utils to generate and manipulate strings."""

import json
import random
import string
from typing import Any


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

    result = "".join((random.choice(alphabet) for _ in range(length)))
    return result


def _format_data(data: Any) -> Any:
    if isinstance(data, dict):
        return {k: _format_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_format_data(v) for v in data]
    elif isinstance(data, bytes):
        return f"<bytes of length {len(data)}>"
    elif isinstance(data, str):
        if len(data) > 4096:
            return f"{data[:256]}... <string of length {len(data)}>"
        else:
            return data
    else:
        return data


def format_dict(dict_obj: dict[str, Any]) -> str:
    """Format message for logging, filtering out large values."""
    filtered_data = _format_data(dict_obj)
    return json.dumps(filtered_data, indent=2)
