import io

from .asset import Asset


class AndroidApk(Asset):
    """Android APK target asset."""
    file: io.FileIO

    def __init__(self, file):
        self.file = file
