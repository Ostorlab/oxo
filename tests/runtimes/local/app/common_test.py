"""Unit tests for common.py."""

from ostorlab.runtimes.local.app import common


def testComputeCvssv3BaseScore_whenVectorIsValid_returnTheRightScore() -> None:
    """Test that the function returns the right score when the vector is valid."""
    vector = "CVSS:3.0/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
    expected_score = 9.8

    assert common.compute_cvss_v3_base_score(vector) == expected_score


def testComputeCvssv3BaseScore_whenVectorIsInvalid_returnNone() -> None:
    """Test that the function returns None when the vector is invalid."""
    vector = "INVALID:VECTOR"

    assert common.compute_cvss_v3_base_score(vector) is None


def testComputeCvssv3BaseScore_whenVectorIsNone_returnNone() -> None:
    """Test that the function returns None when the vector is None."""
    vector = None

    assert common.compute_cvss_v3_base_score(vector) is None
