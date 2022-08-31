"""File asset."""

from typing import Optional

from ostorlab.assets import asset


@asset.selector('v3.asset.file')
class File(asset.Asset):
    """File target asset."""

    def __init__(self, content: bytes, path: Optional[str] = None):
        self.content = content
        self.path = path

    def __str__(self):
        return f'File({self.path})'
