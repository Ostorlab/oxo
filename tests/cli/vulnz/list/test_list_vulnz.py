"""Tests for vulnz list command."""
from unittest import mock

from click.testing import CliRunner

from ostorlab.cli import rootcli
from ostorlab.runtimes.local.models import models


@mock.patch('ostorlab.runtimes.local.models.models.ENGINE_URL', 'sqlite:////tmp/ostorlab_db_cli.sqlite')
def testOstorlabVulnzListCLI_whenCorrectCommandsAndOptionsProvided_showsVulnzInfo():
    """Test ostorlab vulnz list command with correct commands and options.
    Should show vulnz information.
    """
    runner = CliRunner()
    models.Database().create_db_tables()
    create_scan_db = models.Scan.create('test')
    vuln_db = models.Vulnerability.create(title='MyVuln', short_description= 'Xss', description= 'Javascript Vuln',
    recommendation= 'Sanitize data', technical_detail= 'a=$input', risk_rating= 'HIGH',
    cvss_v3_vector= '5:6:7', dna= '121312', scan_id=create_scan_db.id)
    result = runner.invoke(rootcli.rootcli, ['vulnz', 'list', '-s', str(vuln_db.scan_id) ])
    assert vuln_db.scan_id is not None
    assert result.exception is None
    assert 'MyVuln' in result.output
    assert '[bold red]High[/]' in result.output
