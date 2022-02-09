import semver

class Version:

    def __init__(self, version: str) -> None:
        semver.parse(version)
        self._version = version

    def __repr__(self):
        return f'<Version {self._version}>'

    def __lt__(self, other):
        if isinstance(other, Version):
            return semver.compare(self._version, other._version) < 0
        else:
            raise ValueError()

    def __le__(self, other):
        if isinstance(other, Version):
            return semver.compare(self._version, other._version) <= 0
        else:
            raise ValueError()

    def __gt__(self, other):
        if isinstance(other, Version):
            return semver.compare(self._version, other._version) > 0
        else:
            raise ValueError()

    def __ge__(self, other):
        if isinstance(other, Version):
            return semver.compare(self._version, other._version) >= 0
        else:
            raise ValueError()

    def __eq__(self, other):
        if isinstance(other, Version):
            return self._version == other._version
        else:
            raise ValueError()


