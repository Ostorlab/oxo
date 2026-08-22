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
