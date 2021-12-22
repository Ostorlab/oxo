import pytest

from ostorlab.utils import strings


def testRandomString_whenLengthIsValid_returnsARandomStringOfSpecifiedSize():
    generated = strings.random_string(6)

    assert isinstance(generated, str)
    assert len(generated) == 6


def testRandomString_whenLengthIsInvalid_raisesAnException():
    with pytest.raises(ValueError):
        strings.random_string(0)

