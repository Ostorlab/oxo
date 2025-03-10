"""Unit tests for common utilities for scan run assets."""

import pathlib
import hashlib

import pytest
import requests
from pytest_mock import MockerFixture

from ostorlab.cli.scan.run.assets import common
from ostorlab import exceptions


def testDownloadFile_whenRequestIsSuccessful_shouldReturnContent(
    tmp_path: pathlib.Path, mocker: MockerFixture
) -> None:
    """Test download_file returns content when the request is successful."""
    test_url = "https://example.com/test.file"
    save_path = tmp_path / "test.file"
    mock_response = mocker.Mock()
    mock_response.content = b"test content"
    mock_get = mocker.patch("requests.get", return_value=mock_response)

    result = common.download_file(test_url, save_path)

    mock_get.assert_called_once_with(test_url, timeout=900.0)
    assert result == b"test content"
    assert save_path.read_bytes() == b"test content"


def testDownloadFile_whenFileExists_shouldReturnExistingContent(
    tmp_path: pathlib.Path, mocker: MockerFixture
) -> None:
    """Test download_file returns existing content when the file already exists."""
    test_url = "https://example.com/test.file"
    save_path = tmp_path / "test.file"
    save_path.write_bytes(b"existing content")
    mock_get = mocker.patch("requests.get")

    result = common.download_file(test_url, save_path)

    mock_get.assert_not_called()
    assert result == b"existing content"
    assert save_path.read_bytes() == b"existing content"


def testDownloadFile_whenRequestFails_shouldRaiseException(
    tmp_path: pathlib.Path, mocker: MockerFixture
) -> None:
    """Test download_file raises OstorlabError when the request fails."""
    test_url = "https://example.com/test.file"
    save_path = tmp_path / "test.file"
    mocker.patch(
        "requests.get",
        side_effect=requests.exceptions.RequestException("Connection error"),
    )

    with pytest.raises(exceptions.OstorlabError) as exc_info:
        common.download_file(test_url, save_path)

    assert "Failed to download file" in str(exc_info.value)
    assert "Connection error" in str(exc_info.value)
    assert save_path.exists() is False


def testHashUrl_always_shouldReturnMd5Hash() -> None:
    """Test hash_url returns the correct MD5 hash of a URL."""
    test_url = "https://example.com/test.file"
    expected_hash = hashlib.md5(test_url.encode("utf-8")).hexdigest()

    result = common.hash_url(test_url)

    assert result == expected_hash
    assert len(result) == 32  # MD5 hash is 32 characters long


def testHashUrl_whenDifferentUrls_shouldProduceDifferentHashes() -> None:
    """Test hash_url produces different hashes for different URLs."""
    url1 = "https://example.com/file1.txt"
    url2 = "https://example.com/file2.txt"

    hash1 = common.hash_url(url1)
    hash2 = common.hash_url(url2)

    assert hash1 != hash2


def testHashUrl_whenSameUrls_shouldProduceSameHash() -> None:
    """Test hash_url produces the same hash for identical URLs."""
    url = "https://example.com/file.txt"

    hash1 = common.hash_url(url)
    hash2 = common.hash_url(url)

    assert hash1 == hash2
