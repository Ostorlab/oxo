"""Module contains all the supported assets that we can pass to the scan command."""

from ostorlab.cli.scan.run.assets import agent
from ostorlab.cli.scan.run.assets import android_aab
from ostorlab.cli.scan.run.assets import android_apk
from ostorlab.cli.scan.run.assets import android_store
from ostorlab.cli.scan.run.assets import api_schema
from ostorlab.cli.scan.run.assets import domain_name
from ostorlab.cli.scan.run.assets import file
from ostorlab.cli.scan.run.assets import harmonyos_aab
from ostorlab.cli.scan.run.assets import harmonyos_apk
from ostorlab.cli.scan.run.assets import harmonyos_app
from ostorlab.cli.scan.run.assets import harmonyos_hap
from ostorlab.cli.scan.run.assets import harmonyos_rpk
from ostorlab.cli.scan.run.assets import harmonyos_store
from ostorlab.cli.scan.run.assets import ios_ipa
from ostorlab.cli.scan.run.assets import ios_store
from ostorlab.cli.scan.run.assets import ios_testflight
from ostorlab.cli.scan.run.assets import ip
from ostorlab.cli.scan.run.assets import link
from ostorlab.cli.scan.run.assets import message
from ostorlab.cli.scan.run.assets import phone_number
from ostorlab.cli.scan.run.assets import repository
from ostorlab.cli.scan.run.assets import repository_archive
from ostorlab.cli.scan.run.assets import risk
from ostorlab.cli.scan.run.assets import ticket

__all__ = (
    "agent",
    "android_aab",
    "android_apk",
    "android_store",
    "api_schema",
    "domain_name",
    "file",
    "harmonyos_aab",
    "harmonyos_apk",
    "harmonyos_app",
    "harmonyos_hap",
    "harmonyos_rpk",
    "harmonyos_store",
    "ios_ipa",
    "ios_store",
    "ios_testflight",
    "ip",
    "link",
    "message",
    "phone_number",
    "repository",
    "repository_archive",
    "risk",
    "ticket",
)
