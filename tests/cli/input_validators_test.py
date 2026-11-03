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


def testValidateLabels_whenEqualsSeparatorAndColonInValue_splitsOnFirstEquals() -> None:
    result = input_validators.validate_labels(None, "", ("key=http://host:8080",))
    assert result == {"key": "http://host:8080"}


def testValidateLabels_whenEmptyKeyWithColon_raisesUsageError() -> None:
    with pytest.raises(click.UsageError):
        input_validators.validate_labels(None, "", (":value",))


def testValidateLabels_whenEmptyKeyWithEquals_raisesUsageError() -> None:
    with pytest.raises(click.UsageError):
        input_validators.validate_labels(None, "", ("=value",))


def testValidatePortBindingInput_whenNoneValue_returnsNone() -> None:
    assert input_validators.validate_port_binding_input(None, "", None) is None


def testValidatePortBindingInput_whenSingleBinding_returnsValue() -> None:
    result = input_validators.validate_port_binding_input(None, "", "5672:5672")
    assert result == "5672:5672"


def testValidatePortBindingInput_whenMoreThanTwoBindings_returnsValue() -> None:
    value = "5672:5672,15672:15672,25672:25672"
    result = input_validators.validate_port_binding_input(None, "", value)
    assert result == value


@pytest.mark.parametrize(
    "value", ["5672", "5672:", "a:5672", "5672:5672,", "5672:5672;15672:15672"]
)
def testValidatePortBindingInput_whenInvalidSyntax_raisesUsageError(value: str) -> None:
    with pytest.raises(click.UsageError):
        input_validators.validate_port_binding_input(None, "", value)


@pytest.mark.parametrize(
    "url",
    [
        "https://api.example.com/apis/graphql",
        "http://localhost:8000/orchestrator/graphql",
    ],
)
def testValidateEngineUrl_whenAbsoluteHttpUrl_returnsUrl(url: str) -> None:
    assert (
        input_validators.validate_engine_url(None, "reporting_engine_url", url) == url
    )


def testValidateEngineUrl_whenNoneValue_returnsNone() -> None:
    assert (
        input_validators.validate_engine_url(None, "reporting_engine_url", None) is None
    )


@pytest.mark.parametrize(
    "url", ["api.example.com/apis/graphql", "ftp://example.com/graphql", "https://"]
)
def testValidateEngineUrl_whenNotAbsoluteHttpUrl_raisesBadParameter(url: str) -> None:
    with pytest.raises(click.BadParameter):
        input_validators.validate_engine_url(None, "reporting_engine_url", url)


def testValidateEngineUrl_whenHttpToRemoteHost_raisesBadParameter() -> None:
    with pytest.raises(click.BadParameter, match="must use https"):
        input_validators.validate_engine_url(
            None, "reporting_engine_url", "http://re.example.com/apis/graphql"
        )
