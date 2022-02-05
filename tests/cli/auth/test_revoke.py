"""Unit Tests for auth revoke command."""

from click.testing import CliRunner
from unittest import mock

from ostorlab.cli import rootcli
from ostorlab import configuration_manager
from ostorlab.apis.runners import authenticated_runner


def testOstorlabAuthRevokeCLI_whenValidApiKeyIdIsProvided_apiDataDeleted(requests_mock):
    """Test ostorlab auth revoke command with valid api key id.
    Should delete api data from storage.
    """

    api_data_dict = {'data': {'revokeApiKey': {'result': True}}}
    runner = CliRunner()
    requests_mock.post(authenticated_runner.AUTHENTICATED_GRAPHQL_ENDPOINT,
                       json=api_data_dict, status_code=200)
    result = runner.invoke(rootcli.rootcli, ['auth', 'revoke'])

    assert result.exception is None
    assert configuration_manager.ConfigurationManager(
    ).get_api_data() is None


@mock.patch.object(authenticated_runner.AuthenticatedAPIRunner, 'unauthenticate')
def testOstorlabAuthRevokeCLI_whenInvalidApiKeyIdIsProvided_logsError(
    mock_console, requests_mock):
    """Test ostorlab auth revoke command with wrong api key id.
    Should unauthenticate user.
    """

    errors_dict = {'errors': [{'message': 'OrganizationAPIKey matching query does not exist.', 'locations': [
        {'line': 3, 'column': 16}], 'path': ['revokeApiKey']}], 'data': {'revokeApiKey': None}}

    mock_console.return_value = None
    runner = CliRunner()
    requests_mock.post(authenticated_runner.AUTHENTICATED_GRAPHQL_ENDPOINT,
                       json=errors_dict, status_code=200)
    result = runner.invoke(rootcli.rootcli, ['auth', 'revoke'])
    assert result.exception is None
    mock_console.assert_called()


