"""Tests for scan list command."""
from click.testing import CliRunner
from ostorlab.cli import rootcli
from ostorlab.cli import console

from unittest import mock


def testOstorlabScanListCLI_whenNoOptionsProvided_showsUsage():
    """Test ostorlab scan command with no options and no sub command.
    Should show usage.
    """

    runner = CliRunner()

    result = runner.invoke(rootcli.rootcli, ['scan', 'list'])

    assert 'Usage: rootcli scan list [OPTIONS]\n' in result.output


scans_data = {
    "data": {
        "scans": {
            "pageInfo": {
                "hasNext": True,
                "hasPrevious": False,
                "count": 2579,
                "numPages": 2579
            },
            "scans": [
                {
                    "assetType": "ios_store",
                    "riskRating": None,
                    "version": None,
                    "packageName": None,
                    "id": "5040",
                    "progress": "not_started",
                    "createdTime": "2022-01-04T12:00:24.548386+00:00",
                    "plan": "FREE",
                    "asset": {
                        "__typename": "IOSStoreAssetType",
                        "applicationName": "Drop a Message",
                        "packageName": "com.adrianeio.dropamessage"
                    }
                }
            ]
        }
    }
}

def testOstorlabAuthRevokeCLI_whenInvalidApiKeyIdIsProvided_logsError(
        mock_rich_console, requests_mock):
    """Test ostorlab auth revoke command with wrong api key id.
    Should log the error.
    """

    errors_dict = {'errors': [{'message': 'OrganizationAPIKey matching query does not exist.', 'locations': [
        {'line': 3, 'column': 16}], 'path': ['revokeApiKey']}], 'data': {'revokeApiKey': None}}

    mock_rich_console.return_value = None
    runner = CliRunner()
    requests_mock.post(api_request.AUTHENTICATED_GRAPHQL_ENDPOINT,
                       json=errors_dict, status_code=200)
    result = runner.invoke(rootcli.rootcli, ['auth', 'revoke'])
    assert result.exception is None
    mock_rich_console.assert_called_once_with('Could not revoke your API key.')
