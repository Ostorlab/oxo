"""Unit tests for the definitions module."""

from ostorlab.utils import definitions

def testArgConvertStr_whenTargetTypeIsNumber_returnsInt():
    """Test convert_str for number type."""
    assert definitions.Arg.convert_str("18439", "number") == 18439
    assert isinstance(definitions.Arg.convert_str("18439", "number"), int)

def testArgConvertStr_whenTargetTypeIsInt_returnsInt():
    """Test convert_str for int type."""
    assert definitions.Arg.convert_str("18439", "int") == 18439
    assert isinstance(definitions.Arg.convert_str("18439", "int"), int)
