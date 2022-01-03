"""Unit Tests for auth revoke command."""

import logging

from click.testing import CliRunner
from ostorlab.cli import rootcli
from ostorlab import configuration_manager
from ostorlab.apis import request as api_request

from unittest import mock


def testOstorlabAuthRevokeCLI_whenValidApiKeyIdIsProvided_apiDataDeleted(requests_mock):
    """Test ostorlab auth revoke command with valid api key id.
    Should delete api data from storage.
    """

    api_data_dict = {'data': {'revokeApiKey': {'result': True}}}
    runner = CliRunner()
    requests_mock.post(api_request.AUTHENTICATED_GRAPHQL_ENDPOINT,
                       json=api_data_dict, status_code=200)
    result = runner.invoke(rootcli.rootcli, ['auth', 'revoke'])

    assert result.exception is None
    assert configuration_manager.ConfigurationManager(
    ).get_api_data() is None


@mock.patch.object(logging.Logger, 'error')
def testOstorlabAuthRevokeCLI_whenInvalidApiKeyIdIsProvided_logsError(
    mock_logger, requests_mock):
    """Test ostorlab auth revoke command with wrong api key id.
    Should log the error.
    """

    errors_dict = {'errors': [{'message': 'OrganizationAPIKey matching query does not exist.', 'locations': [
        {'line': 3, 'column': 16}], 'path': ['revokeApiKey']}], 'data': {'revokeApiKey': None}}

    mock_logger.return_value = None
    runner = CliRunner()
    requests_mock.post(api_request.AUTHENTICATED_GRAPHQL_ENDPOINT,
                       json=errors_dict, status_code=200)
    result = runner.invoke(rootcli.rootcli, ['auth', 'revoke'])
    assert result.exception is None
    mock_logger.assert_called_once_with('Error revoking your API key.')


