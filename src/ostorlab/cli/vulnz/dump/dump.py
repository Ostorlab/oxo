"""Vulnz dump command."""

import logging

import click
import sqlalchemy
from ostorlab.apis.runners import runner

from ostorlab.cli import console as cli_console
from ostorlab.cli import dumpers
from ostorlab.cli.vulnz import vulnz

console = cli_console.Console()

logger = logging.getLogger(__name__)


@vulnz.command(name="dump")
@click.option("--scan-id", "-s", "scan_id", help="Id of the scan.", required=True)
@click.option(
    "--output", "-o", help="Output file path", required=False, default="./output"
)
@click.option(
    "--format",
    "-f",
    "output_format",
    help="Output format",
    required=False,
    type=click.Choice(["jsonl", "csv"]),
    default="jsonl",
)
@click.pass_context
def dump(ctx, scan_id: int, output: str, output_format: str) -> None:
    """Dump found vulnerabilities of a scan in a specific format."""
    try:
        runtime_instance = ctx.obj["runtime"]
        if output_format == "csv":
            dumper = dumpers.VulnzCsvDumper(output)
        else:
            dumper = dumpers.VulnzJsonDumper(output)
        runtime_instance.dump_vulnz(scan_id=scan_id, dumper=dumper)
    except FileNotFoundError as e:
        console.error(f"No such file or directory: {output}")
        raise click.exceptions.Exit(2) from e
    except (sqlalchemy.exc.OperationalError, runner.Error):
        console.error(f"scan with id {scan_id} does not exist.")
