"""Vulnz Describe command."""
import logging
import click

from ostorlab.cli import console as cli_console
from ostorlab.cli.vulnz import vulnz
from ostorlab.runtimes.local.models import models

console = cli_console.Console()

logger = logging.getLogger(__name__)


def _style_risk(risk: str) -> str:
    """Stylize the risk with colors."""
    if risk.upper() == 'HIGH':
        return '[bold red]High[/]'
    elif risk.upper() == 'MEDIUM':
        return '[bold yellow]Medium[/]'
    elif risk.upper() == 'LOW':
        return '[bold bright_yellow]Low[/]'
    else:
        return risk


@vulnz.command(name='describe')
@click.option('--vuln-id', '-v', 'vuln_id', help='Id of the vulnerability.', required=True)
def describe_cli(vuln_id: int) -> None:
    """CLI command to describe a vulnerability."""
    database = models.Database()
    session = database.session
    vulnerability = session.query(models.Vulnerability).get(vuln_id)
    console.success('Vulnerabilities retrieved successfully.')
    vulnz_list = [
        {'id': str(vulnerability.id),
            'risk_rating': _style_risk(vulnerability.risk_rating.value),
            'cvss_v3_vector': vulnerability.cvss_v3_vector,
            'title': vulnerability.title,
            'short_description': vulnerability.short_description,
         }
    ]

    columns = {
        'Id': 'id',
        'Title': 'title',
        'Risk rating': 'risk_rating',
        'CVSS V3 Vector': 'cvss_v3_vector',
        'Short Description': 'short_description',
    }
    title = f'Describing vulnerability {vuln_id}'
    console.table(columns=columns, data=vulnz_list, title=title)
    console.info('Description')
    console.print(vulnerability.description)
    console.info('Recommendation')
    console.print(vulnerability.recommendation)
    console.info('Technical details')
    console.print(vulnerability.technical_detail)
