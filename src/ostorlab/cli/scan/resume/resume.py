"""Module for the command resume inside the group scan.
This module takes care of resuming a local scan paused with `oxo scan pause`.
Example of usage:
    - oxo scan resume 4"""

import click
from docker import errors as docker_errors

from ostorlab import exceptions
from ostorlab.cli import console as cli_console
from ostorlab.cli.scan.scan import scan
from ostorlab.runtimes.local import runtime as local_runtime

console = cli_console.Console()


@scan.command()
@click.argument("scan_id", type=int, required=True)
@click.pass_context
def resume(ctx: click.core.Context, scan_id: int) -> None:
    """Resume a scan paused with `oxo scan pause`, from where it was paused.\n
    Usage:\n
        - oxo scan --runtime=local resume 4
    """
    runtime_instance = ctx.obj["runtime"]
    if isinstance(runtime_instance, local_runtime.LocalRuntime) is False:
        raise click.ClickException(
            "Resuming a scan is only supported by the local runtime."
        )
    try:
        runtime_instance.resume(scan_id=scan_id)
    except local_runtime.ScanResumeError as e:
        console.error(f"Could not resume scan {scan_id}: {e}")
        raise click.exceptions.Exit(1) from e
    # The failed start re-raises the error of the step that failed, like a docker error creating the network.
    except (exceptions.OstorlabError, docker_errors.DockerException) as e:
        console.error(
            f"An error was encountered while resuming scan {scan_id}, it is still paused: {e}"
        )
        raise click.exceptions.Exit(1) from e
