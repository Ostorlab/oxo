"""Utils to generate and manipulate strings."""

import random
import string


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
