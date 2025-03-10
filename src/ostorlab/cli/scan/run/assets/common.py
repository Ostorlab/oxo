"""Common utilities for oxo scan run assets."""

import datetime
import hashlib
import pathlib
from typing import Optional

import requests

from ostorlab import exceptions

DOWNLOAD_APP_TIMEOUT = datetime.timedelta(minutes=15)


def download_file(url: str, save_path: pathlib.Path) -> Optional[bytes]:
    """Download a file from a URL and save it to the specified path."""
    # check if the file already exists, if so, return the content
    if save_path.exists() is True:
        return save_path.read_bytes()

    # if the file does not exist, download it from the URL
    try:
        response = requests.get(url, timeout=DOWNLOAD_APP_TIMEOUT.total_seconds())
        response.raise_for_status()
        with open(save_path, "wb") as f:
            f.write(response.content)
        return response.content
    except requests.exceptions.RequestException as e:
        raise exceptions.OstorlabError(
            f"Failed to download file from {url}: {e}"
        ) from e


def hash_url(url: str) -> str:
    """Hash the URL to generate a filename."""
    return hashlib.md5(url.encode("utf-8")).hexdigest()
