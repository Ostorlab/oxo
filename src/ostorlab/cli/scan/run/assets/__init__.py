"""Module contains all the supported assets that we can pass to the scan command."""

from ostorlab.cli.scan.run.assets import agent
from ostorlab.cli.scan.run.assets import android_aab
from ostorlab.cli.scan.run.assets import android_apk
from ostorlab.cli.scan.run.assets import domain_name
from ostorlab.cli.scan.run.assets import file
from ostorlab.cli.scan.run.assets import ios_ipa
from ostorlab.cli.scan.run.assets import ip
from ostorlab.cli.scan.run.assets import link
from ostorlab.cli.scan.run.assets import message
from ostorlab.cli.scan.run.assets import risk
from ostorlab.cli.scan.run.assets import android_store
from ostorlab.cli.scan.run.assets import ios_store
from ostorlab.cli.scan.run.assets import ios_testflight
from ostorlab.cli.scan.run.assets import api_schema
from ostorlab.cli.scan.run.assets import harmonyos_hap
from ostorlab.cli.scan.run.assets import harmonyos_apk
from ostorlab.cli.scan.run.assets import harmonyos_aab
from ostorlab.cli.scan.run.assets import harmonyos_app
from ostorlab.cli.scan.run.assets import harmonyos_rpk
from ostorlab.cli.scan.run.assets import harmonyos_store

__all__ = (
    "agent",
    "android_aab",
    "android_apk",
    "domain_name",
    "file",
    "ios_ipa",
    "ip",
    "link",
    "risk",
    "message",
    "android_store",
    "ios_store",
    "ios_testflight",
    "api_schema",
    "harmonyos_hap",
    "harmonyos_apk",
    "harmonyos_aab",
    "harmonyos_app",
    "harmonyos_rpk",
    "harmonyos_store",
)
