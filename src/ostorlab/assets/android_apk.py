import io

from ostorlab import assets


class AndroidApk(assets.Asset):
    """Android APK target asset."""
    file: io.FileIO