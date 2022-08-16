"""Module offering methods to minify a dictionary,
by truncating its string & bytes values to a specific configurable size.
"""
from typing import Any, Callable, Dict, List, Union
from queue import Queue, Empty

TRUNCATE_SIZE = 256

def truncate_str(value: Union[str, bytes], ) -> Union[str, bytes]:
    """Truncate a string or bytes value.

    Args:
        s: the string or bytes value.
        truncate_size: how much to truncate.

    Returns:
        the truncated string or bytes value.
    """
    if isinstance(value, (str, bytes)):
        value = value[:TRUNCATE_SIZE]
    return value

def minify_dict(value: Any, handler: Callable) -> Dict:
    """Recursive approach to minify dictionary values.

    Args:
        dic: The dictionary to minify.
        handler: Method that will be applyed to all the values.

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


def _nested_set(dic: Dict, keys: List, value: any) -> Dict:
    """Populates value in the correct place following the path."""
    for key in keys[:-1]:
        dic = dic.setdefault(key, {})
    dic[keys[-1]] = value


def minify_dict_tail(dic: Dict, handler: Callable) -> Dict:
    """Iterative approach to minify dictionary values.

    Args:
        dic: The dictionary to minify.
        handler: Method that will be applyed to all the values.

    Returns:
        the minified version of the dict.
    """
    q = Queue()
    for path, value in dic.items():
        q.put(([path], value))

    while True:
        try:
            path, value = q.get_nowait()
            print('get', path, value)
            if isinstance(value, list):
                for i, nested_value in enumerate(value):
                    q.put(([*path, i], nested_value))
            elif isinstance(value, dict):
                for key, nested_value in value.items():
                    print('dict', [*path, key], nested_value)
                    q.put(([*path, key], nested_value))
            else:
                value = handler(value)
                _nested_set(dic, path, value)
        except Empty:
            return dic
