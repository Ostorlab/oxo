"""Repository asset."""

import dataclasses
from typing import Optional

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.asset.repository")
class Repository(asset.Asset):
    """Source code repository target asset."""

    content: Optional[bytes] = None
    content_url: Optional[str] = None
    repo_url: Optional[str] = None
    commit_hash: Optional[str] = None

    def __str__(self) -> str:
        if self.repo_url is not None:
            if self.commit_hash is not None:
                return f"Repository: {self.repo_url}@{self.commit_hash}"
            return f"Repository: {self.repo_url}"
        if self.content_url is not None:
            return f"Repository: {self.content_url}"
        return "Repository"

    @property
    def proto_field(self) -> str:
        return "repository"
