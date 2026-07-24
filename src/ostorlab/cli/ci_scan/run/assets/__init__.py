"""Module contains all the supported assets that we can pass to the ci_scan command."""

from ostorlab.cli.ci_scan.run.assets import android_aab, android_apk, ios_ipa, link

__all__ = ["android_aab", "android_apk", "ios_ipa", "link"]
