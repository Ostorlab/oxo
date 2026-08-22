"""Asset of type Risk."""

import io
import logging
import ipaddress
from typing import Optional, Tuple

import click

from ostorlab.assets import (
    risk as risk_asset,
    ipv4 as ipv4_asset,
    ipv6 as ipv6_asset,
    domain_name as domain_name_asset,
    link as link_asset,
    android_store as android_store_asset,
    ios_store as ios_store_asset,
    ios_testflight as ios_testflight_asset,
    android_apk as android_apk_asset,
    android_aab as android_aab_asset,
    ios_ipa as ios_ipa_asset,
    file as file_asset,
    api_schema as api_schema_asset,
)
from ostorlab.cli.scan.run import run
from ostorlab.cli import console as cli_console
from ostorlab import exceptions

console = cli_console.Console()
logger = logging.getLogger(__name__)


def _parse_ip_target(ip_str: str):
    ip_network = ipaddress.ip_network(ip_str, strict=False)
    if ip_network.version == 4:
        return ipv4_asset.IPv4(
            host=ip_network.network_address.exploded,
            mask=str(ip_network.prefixlen),
        )
    elif ip_network.version == 6:
        return ipv6_asset.IPv6(
            host=ip_network.network_address.exploded,
            mask=str(ip_network.prefixlen),
        )
    raise ValueError(f"Invalid IP address {ip_str}")


@run.run.command(name="risk")
@click.option("--severity", "--rating", "severity", help="Risk severity rating.", required=False)
@click.option("--description", help="Risk description.", required=False)
@click.option("--ip", help="IP address / CIDR target.", required=False)
@click.option("--domain", help="Domain name target.", required=False)
@click.option("--link", "links", help="Link target URL.", multiple=True, required=False)
@click.option("--android-store", help="Android package name target.", required=False)
@click.option("--ios-store", help="iOS bundle id target.", required=False)
@click.option("--ios-testflight", help="iOS TestFlight URL target.", required=False)
@click.option("--android-apk-file", type=click.File(mode="rb"), help="Android APK file target.", required=False)
@click.option("--android-apk-url", help="Android APK URL target.", required=False)
@click.option("--android-aab-file", type=click.File(mode="rb"), help="Android AAB file target.", required=False)
@click.option("--android-aab-url", help="Android AAB URL target.", required=False)
@click.option("--ios-ipa-file", type=click.File(mode="rb"), help="iOS IPA file target.", required=False)
@click.option("--ios-ipa-url", help="iOS IPA URL target.", required=False)
@click.option("--file-url", help="File URL target.", required=False)
@click.option("--file-path", "--file", "file_file", type=click.File(mode="rb"), help="File path target.", required=False)
@click.option("--api-schema-url", help="API Schema URL target.", required=False)
@click.option("--api-schema-file", type=click.File(mode="rb"), help="API Schema file target.", required=False)
@click.option("--api-schema-endpoint", help="API Schema endpoint URL target.", required=False)
@click.pass_context
def risk(
    ctx: click.core.Context,
    severity: Optional[str] = None,
    description: Optional[str] = None,
    ip: Optional[str] = None,
    domain: Optional[str] = None,
    links: Optional[Tuple[str, ...]] = None,
    android_store: Optional[str] = None,
    ios_store: Optional[str] = None,
    ios_testflight: Optional[str] = None,
    android_apk_file: Optional[io.FileIO] = None,
    android_apk_url: Optional[str] = None,
    android_aab_file: Optional[io.FileIO] = None,
    android_aab_url: Optional[str] = None,
    ios_ipa_file: Optional[io.FileIO] = None,
    ios_ipa_url: Optional[str] = None,
    file_url: Optional[str] = None,
    file_file: Optional[io.FileIO] = None,
    api_schema_url: Optional[str] = None,
    api_schema_file: Optional[io.FileIO] = None,
    api_schema_endpoint: Optional[str] = None,
) -> None:
    """Run scan for a Risk asset."""
    runtime = ctx.obj["runtime"]

    if severity is None:
        console.error("Risk asset requires --severity/--rating.")
        raise click.exceptions.Exit(2)
    if description is None:
        console.error("Risk asset requires --description.")
        raise click.exceptions.Exit(2)

    target = None
    if ip is not None:
        target = _parse_ip_target(ip)
    elif domain is not None:
        target = domain_name_asset.DomainName(name=domain)
    elif links is not None and len(links) > 0:
        target = link_asset.Link(url=links[0], method="GET")
    elif android_store is not None:
        target = android_store_asset.AndroidStore(package_name=android_store)
    elif ios_store is not None:
        target = ios_store_asset.IOSStore(bundle_id=ios_store)
    elif ios_testflight is not None:
        target = ios_testflight_asset.IOSTestflight(application_url=ios_testflight)
    elif android_apk_file is not None or android_apk_url is not None:
        target = android_apk_asset.AndroidApk(
            content=android_apk_file.read() if android_apk_file is not None else None,
            path=str(android_apk_file.name) if android_apk_file is not None else None,
            content_url=android_apk_url,
        )
    elif android_aab_file is not None or android_aab_url is not None:
        target = android_aab_asset.AndroidAab(
            content=android_aab_file.read() if android_aab_file is not None else None,
            path=str(android_aab_file.name) if android_aab_file is not None else None,
            content_url=android_aab_url,
        )
    elif ios_ipa_file is not None or ios_ipa_url is not None:
        target = ios_ipa_asset.IOSIpa(
            content=ios_ipa_file.read() if ios_ipa_file is not None else None,
            path=str(ios_ipa_file.name) if ios_ipa_file is not None else None,
            content_url=ios_ipa_url,
        )
    elif file_file is not None or file_url is not None:
        target = file_asset.File(
            content=file_file.read() if file_file is not None else None,
            path=str(file_file.name) if file_file is not None else None,
            content_url=file_url,
        )
    elif api_schema_file is not None or api_schema_url is not None:
        target = api_schema_asset.ApiSchema(
            content=api_schema_file.read() if api_schema_file is not None else None,
            content_url=api_schema_url,
            endpoint_url=api_schema_endpoint or "",
        )

    assets = [risk_asset.Risk(rating=severity, description=description, target=target)]
    logger.debug("scanning assets %s", [str(a) for a in assets])
    try:
        created_scan = runtime.scan(
            title=ctx.obj["title"],
            agent_group_definition=ctx.obj["agent_group_definition"],
            assets=assets,
        )
        if created_scan is not None:
            runtime.link_agent_group_scan(
                created_scan, ctx.obj["agent_group_definition"]
            )
            runtime.link_assets_scan(created_scan.id, assets)
    except exceptions.OstorlabError as e:
        console.error(f"An error was encountered while running the scan: {e}")
