"""Version utility class to make easy to compare semantic version strings."""

from semver import version as semver_version


class Version:
    """Version class that only accepts semantic and provides python comparison API."""

    def __init__(self, version: str) -> None:
        """Init version."""
        self._version = version
        self._semver = semver_version.Version.parse(version)

    def __repr__(self) -> str:
        """Version string representation."""
        return f"<Version {self._version}>"

    def __str__(self) -> str:
        """Version string"""
        return self._version

    def __lt__(self, other: object) -> bool:
        """Pythonic comparison API."""
        if isinstance(other, Version):
            return bool(self._semver.compare(other._version) < 0)
        else:
            raise ValueError()

    def __le__(self, other: object) -> bool:
        """Pythonic comparison API."""
        if isinstance(other, Version):
            return bool(self._semver.compare(other._version) <= 0)
        else:
            raise ValueError()

    def __gt__(self, other: object) -> bool:
        """Pythonic comparison API."""
        if isinstance(other, Version):
            return bool(self._semver.compare(other._version) > 0)
        else:
            raise ValueError()

    def __ge__(self, other: object) -> bool:
        """Pythonic comparison API."""
        if isinstance(other, Version):
            return bool(self._semver.compare(other._version) >= 0)
        else:
            raise ValueError()

    def __eq__(self, other: object) -> bool:
        """Pythonic comparison API."""
        if isinstance(other, Version):
            return bool(self._version == other._version)
        else:
            raise ValueError()
