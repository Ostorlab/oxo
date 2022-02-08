"""Vulnz List command."""
import logging
import click

from rich import markdown

from ostorlab.cli import console as cli_console
from ostorlab.cli.vulnz import vulnz
from ostorlab.runtimes.local.models import models
from ostorlab.utils import styles

console = cli_console.Console()

logger = logging.getLogger(__name__)


@vulnz.command(name='list')
@click.option('--scan-id', '-s', 'scan_id', help='Id of the scan.', required=True)
def list_cli(scan_id: int) -> None:
    """CLI command to list vulnerabilities for a scan."""
    database = models.Database()
    session = database.session
    vulnerabilities = session.query(models.Vulnerability).filter_by(scan_id=scan_id).\
        order_by(models.Vulnerability.title).all()
    console.success('Vulnerabilities listed successfully.')
    vulnz_list = []
    for vulnerability in vulnerabilities:
        vulnz_list.append({
            'id': str(vulnerability.id),
            'risk_rating': styles.style_risk(vulnerability.risk_rating.value),
            'cvss_v3_vector': vulnerability.cvss_v3_vector,
            'title': vulnerability.title,
            'short_description': markdown.Markdown(vulnerability.short_description),
        })

    columns = {
        'Id': 'id',
        'Title': 'title',
        'Risk rating': 'risk_rating',
        'CVSS V3 Vector': 'cvss_v3_vector',
        'Short Description': 'short_description',
    }
    title = f'Listing {len(vulnz_list)} vulnerabilities'
    console.table(columns=columns, data=vulnz_list, title=title)
