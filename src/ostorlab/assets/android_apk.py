"""Android APK target asset."""

import io
from .asset import Asset


class AndroidApk(Asset):
    """Android APK target asset."""
    file: io.FileIO

    def __init__(self, file: io.FileIO) -> None:
        """ initiate AndroidApk Asset

        Args:
            file (io.FileIO): android apk file

        Returns:
            None
        """
        self.file = file
