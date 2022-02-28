"""Vulnz Describe command."""
import logging
import click
from typing import Optional

import rich
from rich import markdown
from rich import panel

from ostorlab.cli import console as cli_console
from ostorlab.cli.vulnz import vulnz
from ostorlab.runtimes.local.models import models
from ostorlab.utils import styles


console = cli_console.Console()

logger = logging.getLogger(__name__)

def _print_vulnerability(vulnerability):
    """Print vulnerability details"""
    if vulnerability is None:
        return

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
    title = f'Describing vulnerability {vulnerability.id}'
    console.table(columns=columns, data=vulnz_list, title=title)
    rich.print(panel.Panel(markdown.Markdown(vulnerability.description), title='Description'))
    rich.print(panel.Panel(markdown.Markdown(vulnerability.recommendation), title='Recommendation'))
    rich.print(panel.Panel(markdown.Markdown(vulnerability.technical_detail), title='Technical details'))


@vulnz.command(name='describe')
@click.option('--vuln-id', '-v', 'vuln_id', help='Id of the vulnerability.', required=False)
@click.option('--scan-id', '-s', 'scan_id', help='Id of the scan.', required=False)
def describe_cli(vuln_id: Optional[int] = None, scan_id: Optional[int] = None) -> None:
    """CLI command to describe a vulnerability."""
    if vuln_id is not None:
        database = models.Database()
        session = database.session
        vulnerability = session.query(models.Vulnerability).get(vuln_id)
        console.success('Vulnerabilities retrieved successfully.')
        _print_vulnerability(vulnerability)
    elif scan_id is not None:
        database = models.Database()
        session = database.session
        vulnerabilities = session.query(models.Vulnerability).filter_by(scan_id=scan_id).\
            order_by(models.Vulnerability.title).all()
        for v in vulnerabilities:
            _print_vulnerability(v)
        console.success('Vulnerabilities listed successfully.')





