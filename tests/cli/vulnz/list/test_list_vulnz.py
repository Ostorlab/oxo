"""Tests for vulnz list command."""
from unittest import mock

from click.testing import CliRunner

from ostorlab.cli import rootcli


@mock.patch('ostorlab.runtimes.local.models.models.ENGINE_URL', 'sqlite:////tmp/ostorlab_db.sqlite')
def testOstorlabVulnzListCLI_whenCorrectCommandsAndOptionsProvided_showsVulnzInfo(vuln_db):
    """Test ostorlab vulnz list command with correct commands and options.
    Should show vulnz information.
    """

    runner = CliRunner()
    result = runner.invoke(rootcli.rootcli, ['vulnz', 'list', '-s', str(vuln_db.scan_id) ])
    assert vuln_db.scan_id is not None
    assert result.exception is None
    assert 'MyVuln' in result.output
    assert 'HIGH' in result.output
