"""Repository asset."""

import dataclasses

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.asset.repository")
class Repository(asset.Asset):
    """Source code repository target asset."""

    repository_url: str = ""
    commit_hash: str = ""

    def __str__(self) -> str:
        if self.repository_url != "":
            if self.commit_hash != "":
                return f"Repository: {self.repository_url}@{self.commit_hash}"
            return f"Repository: {self.repository_url}"
        return "Repository"

    @property
    def origin_url(self) -> str:
        return self.repository_url

    @origin_url.setter
    def origin_url(self, value: str) -> None:
        self.repository_url = value

    @property
    def repo_url(self) -> str:
        return self.repository_url

    @repo_url.setter
    def repo_url(self, value: str) -> None:
        self.repository_url = value

    @property
    def proto_field(self) -> str:
        return "repository"
