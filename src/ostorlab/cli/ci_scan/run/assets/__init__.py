"""Module contains all the supported assets that we can pass to the ci_scan command."""

from ostorlab.cli.ci_scan.run.assets import android_apk
from ostorlab.cli.ci_scan.run.assets import android_aab
from ostorlab.cli.ci_scan.run.assets import ios_ipa
from ostorlab.cli.ci_scan.run.assets import link

__all__ = ["android_apk", "android_aab", "ios_ipa", "link"]
