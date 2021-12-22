"""Android aab  asset."""

import io

from ostorlab.assets.asset import Asset


class AndroidAab(Asset):
    """Android AAB target asset."""
    file: io.FileIO

    def __init__(self, file: io.FileIO) -> None:
        """ initiate AndroidAab Asset

        Args:
            file (io.FileIO): android Aab file

        Returns:
            None
        """
        self.file = file
