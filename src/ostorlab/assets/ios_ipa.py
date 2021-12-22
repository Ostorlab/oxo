"""ios .IPA  asset."""

import io

from ostorlab.assets.asset import Asset


class IOSIpa(Asset):
    """Android ipa target asset."""
    file: io.FileIO

    def __init__(self, file: io.FileIO) -> None:
        """ initiate IOSIpa Asset

        Args:
            file (io.FileIO): ios ipa file

        Returns:
            None
        """
        self.file = file
