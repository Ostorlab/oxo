"""Tests for vulnz list command."""
from click.testing import CliRunner

from ostorlab.cli import rootcli
from ostorlab.runtimes.local.models import models


def testOstorlabVulnzListCLI_whenCorrectCommandsAndOptionsProvided_showsVulnzInfo(mocker, tmpdir, db_engine_path):
    """Test ostorlab vulnz list command with correct commands and options.
    Should show vulnz information.
    """
    runner = CliRunner()
    mocker.patch.object(models, 'ENGINE_URL', db_engine_path)
    models.Database().create_db_tables()
    create_scan_db = models.Scan.create('test')
    vuln_db = models.Vulnerability.create(title='MyVuln', short_description= 'Xss', description= 'Javascript Vuln',
    recommendation= 'Sanitize data', technical_detail= 'a=$input', risk_rating= 'HIGH',
    cvss_v3_vector= '5:6:7', dna= '121312', scan_id=create_scan_db.id)
    result = runner.invoke(rootcli.rootcli, ['vulnz', 'list', '-s', str(vuln_db.scan_id) ])
    assert vuln_db.scan_id is not None
    assert result.exception is None
    assert 'MyVuln' in result.output
    assert 'High' in result.output
