import io

from .asset import Asset


class AndroidAab(Asset):
    """Android AAB target asset."""
    file: io.FileIO

    def __init__(self, file):
        self.file = file
