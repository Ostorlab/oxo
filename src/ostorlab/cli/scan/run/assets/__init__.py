"""Module contains all the supported assets that we can pass to the scan command."""

from ostorlab.cli.scan.run.assets import agent
from ostorlab.cli.scan.run.assets import android_aab
from ostorlab.cli.scan.run.assets import android_apk
from ostorlab.cli.scan.run.assets import domain_name
from ostorlab.cli.scan.run.assets import file
from ostorlab.cli.scan.run.assets import ios_ipa
from ostorlab.cli.scan.run.assets import ip
from ostorlab.cli.scan.run.assets import link
from ostorlab.cli.scan.run.assets import android_store
from ostorlab.cli.scan.run.assets import ios_store
from ostorlab.cli.scan.run.assets import ios_testflight

__all__ = (
    "agent",
    "android_aab",
    "android_apk",
    "domain_name",
    "file",
    "ios_ipa",
    "ip",
    "link",
    "android_store",
    "ios_store",
    "ios_testflight",
)
