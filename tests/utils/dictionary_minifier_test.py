"""Unit test for the dictionary minifier module."""
import json

from ostorlab.utils import dictionary_minifier


def testMinifyDict_whenSimpleDict_shouldMinifyStringValues():
    """Ensure the minify dict method return correct values for a simple dictionary."""
    input_dict = {
        "key1": "very long string value.....",
        "key2": "another very long string value.....",
        "key3": "a third very long string value.....",
    }
    dictionary_minifier.TRUNCATE_SIZE = 5

    minified_dict = dictionary_minifier.minify_dict(
        input_dict, dictionary_minifier.truncate_str
    )

    assert minified_dict == {
        "key1": "very ",
        "key2": "anoth",
        "key3": "a thi",
    }


def testMinifyDict_whenNestedDict_shouldMinifyStringValues():
    """Ensure the minify dict method return correct values for nested dictionaries."""
    input_dict = {
        "key1": "very long string value.....",
        "key2": {"key3": {"key4": "key4 very long string value...."}, "key5": 5},
        "key6": b"a third very long string value.....",
    }
    dictionary_minifier.TRUNCATE_SIZE = 2

    minified_dict = dictionary_minifier.minify_dict(
        input_dict, dictionary_minifier.truncate_str
    )

    assert minified_dict == {
        "key1": "ve",
        "key2": {"key3": {"key4": "ke"}, "key5": 5},
        "key6": "b'",  # pylint: disable=C4001
    }


def testMinifyDict_whenNestedDictsAndList_shouldMinifyStringValues():
    """Ensure the minify dict method return correct values for nested dictionaries and lists."""
    input_dict = {
        "key1": "very long string value.....",
        "key2": {
            "key3": {
                "listValues": [
                    {"key4": "key4 very long string value...."},
                    {"key5": b"key5 very long string value...."},
                    {"key6": 42},
                ]
            },
            "key5": 42,
        },
        "key6": b"a third very long string value.....",
    }
    dictionary_minifier.TRUNCATE_SIZE = 3
    minified_dict = dictionary_minifier.minify_dict(
        input_dict, dictionary_minifier.truncate_str
    )

    assert minified_dict == {
        "key1": "ver",
        "key2": {
            "key3": {
                "listValues": [
                    {"key4": "key"},
                    {"key5": "b'k"},  # pylint: disable=C4001
                    {"key6": 42},
                ]
            },
            "key5": 42,
        },
        "key6": "b'a",  # pylint: disable=C4001
    }


def testMinifyDict_whenBytesValues_shouldConvertToStringAndPassJsonEncoding():
    """Ensure the minify dict method returns a json encodable dictionary."""
    input_dict = {"key1": b"very long string value....."}
    dictionary_minifier.TRUNCATE_SIZE = 3

    minified_dict = dictionary_minifier.minify_dict(
        input_dict, dictionary_minifier.truncate_str
    )
    json_dumped_minified_dict = json.dumps(minified_dict)

    assert json_dumped_minified_dict == '{"key1": "b\'v"}'
