"""Unit tests for common.py."""

import pathlib

import pytest

from ostorlab.serve_app import common


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


@pytest.mark.parametrize(
    "items,per_page, num_pages, expected_pages",
    [
        ([], 1, 1, []),
        ([1, 2, 3, 4, 5], 2, 3, [[1, 2], [3, 4], [5]]),
        ([1, 2, 3, 4, 5], 3, 2, [[1, 2, 3], [4, 5]]),
        ([1, 2, 3, 4, 5], 5, 1, [[1, 2, 3, 4, 5]]),
    ],
)
def testPaginator_always_returnTheRightPages(
    items: list[int], per_page: int, num_pages: int, expected_pages: list[list[int]]
) -> None:
    """Test that the function returns the right page when the page is less than the total."""

    paginator = common.Paginator(items, per_page)

    assert paginator.count == len(items)
    pages = []
    for page_number in range(1, paginator.num_pages + 1):
        page = paginator.page(page_number)
        pages.append(list(page))
        assert page.number == page_number
        assert page.has_next() == (page_number < paginator.num_pages)
        assert page.has_previous() == (page_number > 1)
    assert pages == expected_pages


def testGetPackageName_whenApk_returnPackageName() -> None:
    """Test that the function returns the right package name when the file is an APK."""
    path = pathlib.Path(__file__).parent.parent / "files/test.apk"

    package_name = common.get_package_name(str(path))

    assert package_name == "com.michelin.agpressurecalculator"


def testGetBundleId_whenIpa_returnBundleId() -> None:
    """Test that the function returns the right bundle id when the file is an IPA."""
    path = pathlib.Path(__file__).parent.parent / "files/test.ipa"

    bundle_id = common.get_bundle_id(str(path))

    assert bundle_id == "ostorlab.swiftvulnerableapp"
