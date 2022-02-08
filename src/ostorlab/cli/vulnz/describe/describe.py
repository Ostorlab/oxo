"""Vulnz Describe command."""
import logging
import click

import rich
from rich import markdown
from rich import panel

from ostorlab.cli import console as cli_console
from ostorlab.cli.vulnz import vulnz
from ostorlab.runtimes.local.models import models
from ostorlab.utils import styles


console = cli_console.Console()

logger = logging.getLogger(__name__)


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
            'risk_rating': styles.style_risk(vulnerability.risk_rating.value.upper()),
            'cvss_v3_vector': vulnerability.cvss_v3_vector,
            'title': vulnerability.title,
            'short_description': markdown.Markdown(vulnerability.short_description),
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
    rich.print(panel.Panel(markdown.Markdown(vulnerability.description), title='Description'))
    rich.print(panel.Panel(markdown.Markdown(vulnerability.recommendation), title='Recommendation'))
    rich.print(panel.Panel(markdown.Markdown(vulnerability.technical_detail), title='Technical details'))

