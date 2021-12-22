""" Android .APK asset. """
import dataclasses
import io
from ostorlab.assets.asset import Asset


@dataclasses.dataclass
class AndroidApk(Asset):
    """ Android .APK  target asset. """
    file: io.FileIO
