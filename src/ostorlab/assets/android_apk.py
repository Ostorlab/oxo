"""Android APK  asset."""

import io
from ostorlab.assets.asset import Asset


class AndroidApk(Asset):
    """Android Apk target asset."""
    file: io.FileIO

    def __init__(self, file: io.FileIO) -> None:
        """ initiate AndroidApk Asset

        Args:
            file (io.FileIO): android apk file

        Returns:
            None
        """
        self.file = file
