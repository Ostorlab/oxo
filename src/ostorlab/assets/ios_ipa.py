import io

from ostorlab import assets


class IOSIpa(assets.Asset):
    """iOS IPA target asset."""
    file: io.FileIO
