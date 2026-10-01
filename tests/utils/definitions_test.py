"""Unit tests for the definitions module."""

import pytest

from ostorlab.utils import definitions


def testArgConvertStr_whenTargetTypeIsNumber_returnsInt():
    """Test convert_str for number type."""
    assert definitions.Arg.convert_str("18439", "number") == 18439
    assert isinstance(definitions.Arg.convert_str("18439", "number"), int)


def testArgConvertStr_whenTargetTypeIsInt_returnsInt():
    """Test convert_str for int type."""
    assert definitions.Arg.convert_str("18439", "int") == 18439
    assert isinstance(definitions.Arg.convert_str("18439", "int"), int)


@pytest.mark.parametrize("text,value", [("12.5", 12.5), ("1.25e2", 125.0)])
def testArgConvertStr_withDecimalOrScientificNumber_returnsFloat(
    text: str, value: float
) -> None:
    """Number arguments accept decimals and scientific notation."""
    assert definitions.Arg.convert_str(text, "number") == value


@pytest.mark.parametrize("text,value", [("true", True), ("false", False)])
def testArgBuild_withBoolAlias_returnsBoolean(text: str, value: bool) -> None:
    """The bool alias matches boolean text transport."""
    assert definitions.Arg.build("value", "bool", text).value is value


def testArgConvertStr_withDecimalIntAlias_rejectsNonInteger() -> None:
    """The int alias retains integer-only text parsing."""
    with pytest.raises(ValueError):
        definitions.Arg.convert_str("12.5", "int")
