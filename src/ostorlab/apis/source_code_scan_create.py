"""Create source code scan API.

The platform fetches the code itself through the source code integration of the organisation, so a scan
targets a repository reference instead of an uploaded file.
"""

import dataclasses
import json

from ostorlab.apis import request

REPOSITORIES_PAGE_SIZE = 100


@dataclasses.dataclass(frozen=True)
class Repository:
    """Repository reachable through a source code integration of the organisation."""

    id: str
    full_name: str
    private: bool
    default_branch: str
    url: str
    provider: str


class RepositoriesAPIRequest(request.APIRequest):
    """Search the repositories reachable through the source code integrations of the organisation."""

    def __init__(self, search: str) -> None:
        self._search = search

    @property
    def query(self) -> str:
        """Defines the query to search the repositories.

        Returns:
            The query to search the repositories.
        """
        return """
query Repositories($page: Int, $numberElements: Int, $search: String) {
  repositories(page: $page, numberElements: $numberElements, search: $search) {
    repositories {
      id
      fullName
      private
      defaultBranch
      url
      provider
    }
  }
}
        """

    @property
    def data(self) -> dict[str, str]:
        """Sets the query and variables to search the repositories.

        Returns:
            The query and variables to search the repositories.
        """
        return {
            "query": self.query,
            "variables": json.dumps(
                {
                    "page": 1,
                    "numberElements": REPOSITORIES_PAGE_SIZE,
                    "search": self._search,
                }
            ),
        }


class CreateSourceCodeScanAPIRequest(request.APIRequest):
    """Create a source code scan of a repository reachable through a source code integration."""

    def __init__(
        self,
        repository: Repository,
        scan_profile: str,
        title: str | None = None,
        commit_hash: str | None = None,
        branch_name: str | None = None,
    ) -> None:
        self._repository = repository
        self._scan_profile = scan_profile
        self._title = title
        self._commit_hash = commit_hash
        self._branch_name = branch_name

    @property
    def query(self) -> str:
        """Defines the query to create a source code scan.

        Returns:
            The query to create a source code scan.
        """
        return """
mutation SourceCodeScan($repository: RepositoryInputType!, $scanProfile: String, $title: String, $commitHash: String, $branchName: String) {
  createSourceCodeScan(repository: $repository, scanProfile: $scanProfile, title: $title, commitHash: $commitHash, branchName: $branchName) {
    scan {
      id
    }
  }
}
        """

    @property
    def data(self) -> dict[str, str]:
        """Sets the query and variables to create the source code scan.

        Returns:
            The query and variables to create the source code scan.
        """
        return {
            "query": self.query,
            "variables": json.dumps(
                {
                    "repository": {
                        "id": self._repository.id,
                        "fullName": self._repository.full_name,
                        "private": self._repository.private,
                        "defaultBranch": self._repository.default_branch,
                        "url": self._repository.url,
                        "provider": self._repository.provider,
                    },
                    "scanProfile": self._scan_profile,
                    "title": self._title,
                    "commitHash": self._commit_hash,
                    "branchName": self._branch_name,
                }
            ),
        }
