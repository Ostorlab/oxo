import pathlib

from ostorlab.runtimes.local.models import utils


def testGetPackageName_whenApk_returnPackageName() -> None:
    """Test that the function returns the right package name when the file is an APK."""
    path = pathlib.Path(__file__).parent.parent / "files/test.apk"

    package_name = utils.get_package_name(str(path))

    assert package_name == "com.michelin.agpressurecalculator"


def testGetBundleId_whenIpa_returnBundleId() -> None:
    """Test that the function returns the right bundle id when the file is an IPA."""
    path = pathlib.Path(__file__).parent.parent / "files/test.ipa"

    bundle_id = utils.get_bundle_id(str(path))

    assert bundle_id == "ostorlab.swiftvulnerableapp"
