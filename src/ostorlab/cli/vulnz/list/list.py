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
    "--risk-rating", "-r", "risk_rating", help="Filter vulnerabilities by risk rating."
)
@click.option(
    "--filter-type",
    "-f",
    "filter_type",
    type=click.Choice(["exact", "gte", "lte"]),
    help="Specify the filter type for risk rating (exact, gte for greater than or equal, lte for less than or equal).",
)
@click.option("--title", "-t", help="Filter vulnerabilities by title.")
@click.pass_context
def list_cli(
    ctx: click.core.Context,
    scan_id: int,
    risk_rating: Optional[str],
    filter_type: Optional[str],
    title: Optional[str],
) -> None:
    """CLI command to list vulnerabilities for a scan."""
    runtime_instance = ctx.obj["runtime"]
    console.info(f"Fetching vulnerabilities for scan {scan_id}")

    if risk_rating is None and filter_type is not None:
        raise click.BadOptionUsage(
            "filter-type", "--filter-type / -f can only be used with risk-rating"
        )

    runtime_instance.list_vulnz(
        scan_id=scan_id,
        filter_risk_rating=risk_rating,
        filter_type=filter_type or "exact",
        title=title,
    )
