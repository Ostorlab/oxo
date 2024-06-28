"""Utilities for the local runtime models."""

import zipfile

import pyaxmlparser
import plistlib


def get_package_name(path: str) -> str:
    """Get the package name of an android file.

    Args:
        path: Path to the android file.

    Returns:
        str: Package name of the android file.
    """

    apk_info = pyaxmlparser.APK(path)
    return apk_info.get_package()


def get_bundle_id(path: str) -> str:
    """Get the bundle identifier of an iOS ipa file.

    Args:
        path: Path to the iOS ipa file.

    Returns:
        str: Bundle identifier of the iOS ipa file.
    """

    with zipfile.ZipFile(path, "r") as z:
        # Locate the Info.plist file within the IPA
        infoplist = None
        for filename in z.namelist():
            dirs = filename.split("/")
            # payload, Payload and payLoad the three formats can be found
            if (
                len(dirs) == 3
                and dirs[0].lower().strip() == "payload"
                and dirs[2].lower().strip() == "info.plist"
            ):
                content = z.open(filename).read()
                infoplist = plistlib.loads(content)

        if infoplist is None:
            return ""

        # Extract and read the Info.plist file
        bundle_id = infoplist.get("CFBundleIdentifier")
        if bundle_id is None:
            return ""

        return bundle_id
