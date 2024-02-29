"""Vulnz List command."""

import logging
from typing import Optional

import click

from ostorlab.cli import console as cli_console
from ostorlab.cli.vulnz import vulnz

console = cli_console.Console()

logger = logging.getLogger(__name__)


@vulnz.command(name="list")
@click.option("--scan-id", "-s", "scan_id", help="Id of the scan.", required=True)
@click.option(
    "--risk-rating",
    "-r",
    "risk_rating",
    help="Filter vulnerabilities by risk ratings. Accept comma-separated ratings.",
)
@click.option("--search", "-sh", help="Search in all content of the vulnerabilities.")
@click.pass_context
def list_cli(
    ctx: click.core.Context,
    scan_id: int,
    risk_rating: Optional[str],
    search: Optional[str],
) -> None:
    """CLI command to list vulnerabilities for a scan."""
    runtime_instance = ctx.obj["runtime"]
    console.info(f"Fetching vulnerabilities for scan {scan_id}")
    runtime_instance.list_vulnz(
        scan_id=scan_id,
        filter_risk_rating=risk_rating.strip().split(",") if risk_rating else None,
        search=search,
    )
