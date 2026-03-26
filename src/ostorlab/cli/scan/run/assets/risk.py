"""Asset of type Risk.
This module takes care of preparing a risk message to be injected onto the message bus."""

import io
import ipaddress
import logging
from typing import Optional

import click

from ostorlab.assets import risk as risk_asset
from ostorlab.cli import console as cli_console
from ostorlab.cli.scan.run import run
from ostorlab import exceptions

logger = logging.getLogger(__name__)
console = cli_console.Console()


@run.run.command(name="risk")
@click.option(
    "--severity",
    required=True,
    help="Risk severity (e.g., HIGH, CRITICAL, MEDIUM, LOW).",
)
@click.option(
    "--description",
    required=False,
    default=None,
    help="Description of the risk.",
)
@click.option(
    "--description-file",
    type=click.File(mode="r"),
    required=False,
    default=None,
    help="Path to a file containing the risk description.",
)
@click.option(
    "--ip",
    "ip_addr",
    required=False,
    default=None,
    help="IP address the risk applies to.",
)
@click.option(
    "--domain",
    required=False,
    default=None,
    help="Domain name the risk applies to.",
)
@click.option(
    "--link",
    "url",
    required=False,
    default=None,
    help="URL the risk applies to.",
)
@click.option(
    "--android-store",
    required=False,
    default=None,
    help="Android package name the risk applies to.",
)
@click.option(
    "--ios-store",
    required=False,
    default=None,
    help="iOS bundle ID the risk applies to.",
)
@click.pass_context
def risk_cli(
    ctx: click.core.Context,
    severity: str,
    description: Optional[str],
    description_file: Optional[io.TextIOWrapper],
    ip_addr: Optional[str],
    domain: Optional[str],
    url: Optional[str],
    android_store: Optional[str],
    ios_store: Optional[str],
) -> None:
    """Run scan with a risk report injected onto the message bus.\n
    Example:\n
        - oxo scan run --agent=agent/ostorlab/nmap risk --severity HIGH --description "Server exposed" --ip 8.8.8.8\n
        - oxo scan run --agent=agent/ostorlab/nmap risk --severity HIGH --description-file report.txt --ip 8.8.8.8
    """
    if description is None and description_file is None:
        console.error("Provide either --description or --description-file.")
        raise click.exceptions.Exit(2)
    if description is not None and description_file is not None:
        console.error("Provide either --description or --description-file, not both.")
        raise click.exceptions.Exit(2)
    if description_file is not None:
        description = description_file.read()

    runtime = ctx.obj["runtime"]

    risk_kwargs = {
        "description": description,
        "rating": severity,
    }

    if ip_addr is not None:
        try:
            ip_network = ipaddress.ip_network(ip_addr, strict=False)
        except ValueError:
            console.error(f"Invalid IP address: {ip_addr}")
            raise click.exceptions.Exit(2)
        if ip_network.version == 4:
            risk_kwargs["ipv4"] = {
                "host": ip_network.network_address.exploded,
                "mask": str(ip_network.prefixlen),
                "version": 4,
            }
        elif ip_network.version == 6:
            risk_kwargs["ipv6"] = {
                "host": ip_network.network_address.exploded,
                "mask": str(ip_network.prefixlen),
                "version": 6,
            }

    if domain is not None:
        risk_kwargs["domain_name"] = {"name": domain}

    if url is not None:
        risk_kwargs["link"] = {"url": url, "method": "GET"}

    if android_store is not None:
        risk_kwargs["android_store"] = {"package_name": android_store}

    if ios_store is not None:
        risk_kwargs["ios_store"] = {"bundle_id": ios_store}

    assets = [risk_asset.Risk(**risk_kwargs)]

    logger.debug("injecting risk asset %s", assets)
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
