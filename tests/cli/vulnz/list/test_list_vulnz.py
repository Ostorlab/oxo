"""Tests for vulnz list command."""
from click.testing import CliRunner

from ostorlab.apis.runners import authenticated_runner
from ostorlab.cli import rootcli
from ostorlab.runtimes.local.models import models


def testOstorlabVulnzListCLI_whenCorrectCommandsAndOptionsProvidedAndRuntimeIsLocal_showsVulnzInfo(mocker
                                                                                                   , db_engine_path):
    """Test ostorlab vulnz list command with correct commands and options.
    Should show vulnz information.
    """
    runner = CliRunner()
    mocker.patch.object(models, 'ENGINE_URL', db_engine_path)
    models.Database().create_db_tables()
    create_scan_db = models.Scan.create('test')
    vuln_db = models.Vulnerability.create(title='MyVuln', short_description='Xss', description='Javascript Vuln',
                                          recommendation='Sanitize data', technical_detail='a=$input',
                                          risk_rating='HIGH',
                                          cvss_v3_vector='5:6:7', dna='121312', scan_id=create_scan_db.id)
    result = runner.invoke(rootcli.rootcli, ['vulnz', 'list', '-s', str(vuln_db.scan_id)])
    assert vuln_db.scan_id is not None
    assert result.exception is None
    assert 'MyVuln' in result.output
    assert 'High' in result.output


def testOstorlabVulnzListCLI_ScanNotFoundAndRuntimeCloud_showsNotFoundError(requests_mock):
    """"""
    mock_response = {
        'errors': [
            {
                'message': 'Scan matching query does not exist.',
                'locations': [
                    {
                        'line': 2,
                        'column': 13
                    }
                ],
                'path': [
                    'scan'
                ]
            }
        ],
    }
    runner = CliRunner()
    requests_mock.post(authenticated_runner.AUTHENTICATED_GRAPHQL_ENDPOINT,
                       json=mock_response, status_code=401)
    result = runner.invoke(rootcli.rootcli, ['vulnz', '--runtime', 'cloud', 'list', '--scan-id', '56835'])
    assert 'ERROR: scan with id 56835 does not exist.' in result.output, result.output


def testOstorlabVulnzListCLI_WhenRuntimeCloudAndValiScanID_showsVulnzInfo(requests_mock):
    """"""
    mock_response = {
        'data': {
            'scan': {
                'vulnerabilities': {
                    'vulnerabilities': [
                        {
                            'id': '38312829',
                            'detail': {
                                'title': 'Intent Spoofing',
                                'shortDescription': 'The application is vulnerable to intent spoofing which ..',
                                'cvssV3Vector': 'CVSS:3.0/AV:L/AC:H/PR:H/UI:N/S:U/C:H/I:H/A:H',
                                'riskRating': 'POTENTIALLY'
                            }
                        },
                        {
                            'id': '38312828',
                            'detail': {
                                'title': 'Intent Spoofing',
                                'shortDescription': 'The application is vulner...',
                                'cvssV3Vector': 'CVSS:3.0/AV:L/AC:H/PR:H/UI:N/S:U/C:H/I:H/A:H',
                                'riskRating': 'POTENTIALLY'
                            }
                        },
                    ]
                }
            }
        }
    }
    runner = CliRunner()
    requests_mock.post('https://api.ostorlab.co/apis/graphql', json=mock_response)
    result = runner.invoke(rootcli.rootcli, ['vulnz', '--runtime', 'cloud', 'list', '--scan-id', '56835'])
    assert 'Title' in result.output, result.output
    assert 'Scan 56835: Found 2 vulnerabilities' in result.output, result.output
