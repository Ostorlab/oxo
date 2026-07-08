"""Repository asset."""

import dataclasses

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.asset.repository")
class Repository(asset.Asset):
    """Source code repository target asset."""

    repository_url: str = ""
    commit_hash: str = ""
    provider: str = ""
    content_url: str = ""

    def __post_init__(self) -> None:
        if self.repository_url != "" and self.content_url != "":
            raise ValueError(
                "A repository asset must be defined either with repository_url or "
                "content_url, not both."
            )
        if self.repository_url == "" and self.content_url == "":
            raise ValueError(
                "A repository asset requires either repository_url or content_url."
            )
        if self.provider == "":
            del self.provider

    def __str__(self) -> str:
        if self.content_url != "":
            return f"Repository: {self.content_url}"
        if self.commit_hash != "":
            return f"Repository: {self.repository_url}@{self.commit_hash}"
        return f"Repository: {self.repository_url}"

    @property
    def proto_field(self) -> str:
        return "repository"
