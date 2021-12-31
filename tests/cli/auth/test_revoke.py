"""Tests for auth revoke command."""
from click.testing import CliRunner
from ostorlab.cli import rootcli
from ostorlab.apis import runner as apis_runner
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
    ).get_api_data() == None


@mock.patch.object(apis_runner.ResponseError, '__init__')
def testOstorlabAuthRevokeCLI_whenInvalidApiKeyIsProvided_raisesResponseException(
    mock_response_error_init, requests_mock):
    """Test ostorlab auth revoke command with wrong api key id.
    Should raise ResponseError.
    """

    mock_response_error_init.return_value = None
    runner = CliRunner()
    requests_mock.post(api_request.AUTHENTICATED_GRAPHQL_ENDPOINT, json=None, status_code=401)
    result = runner.invoke(rootcli.rootcli, ['auth', 'revoke'])
    assert result.exception is not None
    mock_response_error_init.assert_called()
