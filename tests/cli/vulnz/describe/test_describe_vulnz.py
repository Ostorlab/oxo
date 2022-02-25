"""Tests for vulnz describe command."""
from click.testing import CliRunner

from ostorlab.cli import rootcli
from ostorlab.runtimes.local.models import models


def testOstorlabVulnzListCLI_whenCorrectCommandsAndOptionsProvided_showsVulnzInfo(mocker, tmpdir):
    """Test ostorlab vulnz describe command with correct commands and options.
    Should show vulnz details.
    """
    runner = CliRunner()
    mocker.patch.object(models, 'ENGINE_URL', f'sqlite:////{tmpdir}/ostorlab_db_cli.sqlite')
    models.Database().create_db_tables()
    create_scan_db = models.Scan.create('test')
    vuln_db = models.Vulnerability.create(title='Secure TLS certificate validation',
                                          short_description='Application performs proper server certificate '
                                                             'validation',
                                          description='The application performs proper TLS certificate validation.',
                                          recommendation='The implementation is secure, no recommendation apply.',
                                          technical_detail='TLS certificate validation was tested dynamically by '
                                                            'intercepting traffic and presenting an invalid '
                                                            'certificate. The application refuses to complete TLS '
                                                            'negotiation when the certificate is not signed by '
                                                            'valid authority.',
                                          risk_rating='HIGH',
    cvss_v3_vector= '5:6:7', dna= '121312', scan_id=create_scan_db.id)
    result = runner.invoke(rootcli.rootcli, ['vulnz', 'describe', '-v', str(vuln_db.id) ])
    assert vuln_db.scan_id is not None
    assert result.exception is None
    assert 'The application performs' in result.output
    assert 'TLS certificate validation' in result.output
