"""Repository asset."""

import dataclasses

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.asset.repository")
class Repository(asset.Asset):
    """Source code repository target asset."""

    origin_url: str = ""
    commit_hash: str = ""

    def __str__(self) -> str:
        if self.origin_url != "":
            if self.commit_hash != "":
                return f"Repository: {self.origin_url}@{self.commit_hash}"
            return f"Repository: {self.origin_url}"
        return "Repository"

    @property
    def repo_url(self) -> str:
        return self.origin_url

    @repo_url.setter
    def repo_url(self, value: str) -> None:
        self.origin_url = value

    @property
    def proto_field(self) -> str:
        return "repository"
