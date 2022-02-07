"""Vulnz List command."""
import logging
import click

from ostorlab.cli import console as cli_console
from ostorlab.cli.vulnz import vulnz
from ostorlab.runtimes.local.models import models

console = cli_console.Console()

logger = logging.getLogger(__name__)


def _human_readable_size(size, decimal_places=3):
    for unit in ['B', 'KiB', 'MiB', 'GiB', 'TiB']:
        if size < 1024.0:
            break
        size /= 1024.0
    return f'{size:.{decimal_places}f}{unit}'


@vulnz.command(name='list')
@click.option('--scan-id', '-s', 'scan_id', help='Id of the scan.', required=True)
def list_cli(scan_id: int) -> None:
    """CLI command to list vulnerabilities for a scan."""
    database = models.Database()
    session = database.session
    vulnerabilities = session.query(models.Vulnerability).filter_by(scan_id=scan_id).order_by(models.Vulnerability.title).all()
    console.success('Vulnerabilities listed successfully.')
    vulnz = []
    for vulnerability in vulnerabilities:
        vulnz.append({
            'id': str(vulnerability.id),
            'risk_rating': str(vulnerability.risk_rating),
            'cvss_v3_vector': vulnerability.cvss_v3_vector,
            'title': vulnerability.title,
            'short_description': vulnerability.short_description,
        })

    columns = {
        'Id': 'id',
        'Risk rating': 'risk_rating',
        'CVSS V3 Vector': 'cvss_v3_vector',
        'Title': 'title',
        'Short Description': 'short_description',
    }
    title = f'Listing {len(vulnz)} vulnerabilities'
    console.table(columns=columns, data=vulnz, title=title)
