"""Tests for CLI input validators."""

import click
import pytest

from ostorlab.cli import input_validators


def testValidateLabels_whenValidColonFormat_returnsParsedDict() -> None:
    result: dict[str, str] = input_validators.validate_labels(None, "", ("key:value",))
    assert result == {"key": "value"}


def testValidateLabels_whenValidEqualsFormat_returnsParsedDict() -> None:
    result: dict[str, str] = input_validators.validate_labels(None, "", ("key=value",))
    assert result == {"key": "value"}


def testValidateLabels_whenNoSeparator_raisesUsageError() -> None:
    with pytest.raises(click.UsageError):
        input_validators.validate_labels(None, "", ("invalidlabel",))


def testValidateLabels_whenEmptyTuple_returnsEmptyDict() -> None:
    result: dict[str, str] = input_validators.validate_labels(None, "", ())
    assert result == {}


def testValidateLabels_whenNoneValue_returnsEmptyDict() -> None:
    result: dict[str, str] = input_validators.validate_labels(None, "", None)
    assert result == {}


def testValidateLabels_whenMultipleLabels_returnsAllParsed() -> None:
    result: dict[str, str] = input_validators.validate_labels(
        None, "", ("key1:value1", "key2=value2", "key3:value3")
    )
    assert result == {"key1": "value1", "key2": "value2", "key3": "value3"}


def testValidateLabels_whenColonInValue_splitsOnFirstColonOnly() -> None:
    result: dict[str, str] = input_validators.validate_labels(
        None, "", ("url:http://host:8080",)
    )
    assert result == {"url": "http://host:8080"}


def testValidateLabels_whenEqualsInValue_splitsOnFirstEqualsOnly() -> None:
    result: dict[str, str] = input_validators.validate_labels(
        None, "", ("formula:a=b=c",)
    )
    assert result == {"formula": "a=b=c"}


def testValidateLabels_whenMixedFormats_returnsAllParsed() -> None:
    result: dict[str, str] = input_validators.validate_labels(
        None, "", ("env:production", "version=1.0", "url:http://example.com:8080")
    )
    assert result == {
        "env": "production",
        "version": "1.0",
        "url": "http://example.com:8080",
    }


def testValidateLabels_whenEmptyValue_parsesSuccessfully() -> None:
    result: dict[str, str] = input_validators.validate_labels(None, "", ("key:",))
    assert result == {"key": ""}
