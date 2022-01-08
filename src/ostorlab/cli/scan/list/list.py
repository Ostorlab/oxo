"""Module for the command list inside the group scan.
This module takes care of listing all the remote or local scans.
Example of usage:
    - ostorlab scan list --source=source."""

import click

from ostorlab.cli import console as cli_console
from ostorlab.cli.scan import scan

console = cli_console.Console()


def _style_risk(risk: str) -> str:
    """Stylize the risk with colors."""
    if risk == 'HIGH':
        return '[bold red]High[/]'
    elif risk == 'MEDIUM':
        return '[bold yellow]Medium[/]'
    elif risk == 'LOW':
        return '[bold bright_yellow]Low[/]'
    else:
        return risk


def _style_progress(progress: str) -> str:
    """Stylize the scan progress with colors."""
    if progress == 'done':
        return '[bold green4]Done[/]'
    if progress == 'error':
        return '[bold magenta]Error[/]'
    if progress == 'not_started':
        return '[bold bright_black]Not Started[/]'
    if progress == 'stopped':
        return '[bold bright_red]Stopped[/]'
    if progress == 'in_progress':
        return '[bold bright_cyan]Running[/]'
    else:
        return progress


def _style_asset(asset: str) -> str:
    """Stylize the scan asset with colors and emojis."""
    if asset == 'android_store':
        return '[bold green4]:iphone: Android Store[/]'
    elif asset == 'ios_store':
        return '[bold bright_white]:apple: iOS Store[/]'
    elif asset == 'android':
        return '[bold bright_green]:iphone: Android[/]'
    elif asset == 'ios':
        return '[bold white]:apple: iOS[/]'
    else:
        return asset


@scan.command(name='list')
@click.option('--page', '-p', help='Page number of scans you would like to see.', default=1)
@click.option('--elements', '-e', help='Number of scans to show per page.', default=10)
@click.pass_context
def list_scans(ctx: click.core.Context, page: int, elements: int) -> None:
    """List all your scans.\n
    Usage:\n
        - ostorlab scan list --source=source
    """
    runtime_instance = ctx.obj['runtime']
    with console.status('Fetching scans'):
        scans = runtime_instance.list(page=page, number_elements=elements)
        if scans is not None:
            console.success('Scans listed successfully.')
            columns = {'Id': 'id',
                       'Application': 'application',
                       'Platform': 'platform',
                       'Plan': 'plan',
                       'Created Time': 'created_time',
                       'Progress': 'progress',
                       'Risk': 'risk'}
            title = f'Showing {len(scans)} Scans'

            data = [
                {
                    'id': s.id,
                    'application': f'{s.application or ""}: {s.version or ""}',
                    'platform': _style_asset(s.platform),
                    'plan': s.plan,
                    'created_time': s.created_time,
                    'progress': _style_progress(s.progress),
                    'risk': _style_risk(s.risk),
                } for s in scans]

            console.table(columns=columns, data=data, title=title)
        else:
            console.error('Error fetching scan list.')
