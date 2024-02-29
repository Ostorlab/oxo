"""Module offering methods to minify a dictionary,
by truncating its string & bytes values to a specific configurable size.
"""

from typing import Any, Callable, Dict, List, Union

TRUNCATE_SIZE = 256


def truncate_str(
    value: Union[str, bytes],
) -> Union[str, bytes]:
    """Truncate a string or bytes value.

    Args:
        s: the string or bytes value.
        truncate_size: how much to truncate.

    Returns:
        the truncated string or bytes value.
    """
    if isinstance(value, (str, bytes)):
        # The casting to string is specific to the bytes case, to prevent the json encoding from failing later.
        value = str(value)[:TRUNCATE_SIZE]
    return value


def minify_dict(
    value: Any, handler: Callable[[object], object]
) -> Union[Dict[object, object], List[object], object]:
    """Recursive approach to minify dictionary values.

    Args:
        dic: The dictionary to minify.
        handler: Method that will be applied to all the values.

    Returns:
        the minified version of the dict.
    """
    if isinstance(value, list):
        return [minify_dict(v, handler) for v in value]
    elif isinstance(value, dict):
        for key, v in value.items():
            value[key] = minify_dict(v, handler)
        return value
    else:
        return handler(value)


def _nested_set(dic: Any, keys: List[object], value: Any) -> None:
    """Populates value in the correct place following the path."""
    for key in keys[:-1]:
        dic = dic.setdefault(key, {})
    dic[keys[-1]] = value
