"""Repository asset."""

import dataclasses
from typing import Optional

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.asset.repository")
class Repository(asset.Asset):
    """Source code repository target asset."""

    origin_url: Optional[str] = None
    commit_hash: Optional[str] = None

    def __str__(self) -> str:
        if self.origin_url is not None:
            if self.commit_hash is not None:
                return f"Repository: {self.origin_url}@{self.commit_hash}"
            return f"Repository: {self.origin_url}"
        return "Repository"

    @property
    def repo_url(self) -> Optional[str]:
        return self.origin_url

    @repo_url.setter
    def repo_url(self, value: Optional[str]) -> None:
        self.origin_url = value

    @property
    def proto_field(self) -> str:
        return "repository"
