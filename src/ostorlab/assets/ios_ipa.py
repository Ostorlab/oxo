import io

from ostorlab.assets.asset import Asset


class IOSIpa(Asset):
    """iOS IPA target asset."""
    file: io.FileIO

    def __init__(self, file):
        self.file = file
