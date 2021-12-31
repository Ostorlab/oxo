"""Tests for auth login command."""
from click.testing import CliRunner
from ostorlab.cli import rootcli
from ostorlab.apis import runner as apis_runner
from ostorlab import configuration_manager
from ostorlab.apis import request as api_request

import click
from unittest import mock


def testOstorlabAuthLoginCLI_whenNoOptionsProvided_showsUsage():
    """Test ostorlab auth login command when used with no options.
    Should show usage.
    """

    runner = CliRunner()
    result = runner.invoke(rootcli.rootcli, ['auth', 'login'])

    assert 'Usage: rootcli auth login [OPTIONS]' in result.output
    assert result.exit_code == 2


@mock.patch.object(apis_runner.AuthenticationError, '__init__')
def testOstorlabAuthLoginCLI_whenInvalidLoginCredentialsAreProvided_raisesAuthenticationException(mock_authentication_error_init,
                                                                                                  requests_mock):
    """Test ostorlab auth login command with wrong login credentials.
    Should raise AuthenticationError.
    """

    mock_authentication_error_init.return_value = None
    runner = CliRunner()
    requests_mock.post(api_request.TOKEN_ENDPOINT, json={'non_field_errors': [
                       'Unable to log in with provided credentials.']}, status_code=400)
    result = runner.invoke(
        rootcli.rootcli, ['auth', 'login', '--username=username', '--password=password'])

    assert result.exception is None
    mock_authentication_error_init.assert_called()


def testOstorlabAuthLoginCLI_whenValidLoginCredentialsAreProvided_tokenSet(requests_mock):
    """Test ostorlab auth login command with valid login credentials (no otp required).
    Should set API key.
    """

    api_key_dict = {'data': {'createApiKey': {'apiKey': {
        'secretKey': 'ADABYMTu.S7Y8zmKxpbgTcSuGmsC3rkPdAs95yMwW', 'apiKey': {'expiryDate': None}}}}}
    token_dict = {'token': '2fd7a589-64b4-442e-95aa-eb0d082aab63'}
    runner = CliRunner()
    requests_mock.post(api_request.TOKEN_ENDPOINT, json = token_dict, status_code = 200)
    requests_mock.post(api_request.AUTHENTICATED_GRAPHQL_ENDPOINT, json = api_key_dict, status_code = 200)
    result = runner.invoke(
        rootcli.rootcli, ['auth', 'login', '--username=username', '--password=password'])

    assert result.exception is None
    assert configuration_manager.ConfigurationManager(
    ).get_api_key() == api_key_dict['data']['createApiKey']['apiKey']['secretKey']


@ mock.patch.object(click, 'prompt')
def testOstorlabAuthLoginCLI_whenValidLoginCredentialsAreProvidedWithoutOtp_promptOtp(mock_prompt, requests_mock):
    """Test ostorlab auth login command with correct login credentials without OTP.
    Should assert that the otp prompt is called.
    """

    mock_prompt.return_value = None
    runner = CliRunner()
    token_dict = {'token': '2fd7a589-64b4-442e-95aa-eb0d082aab63'}
    requests_mock.post(api_request.TOKEN_ENDPOINT, [{'json':{'non_field_errors': [
                       'Must include "otp_token"']}, 'status_code':400}, {'json': token_dict, 'status_code': 200}])
    runner.invoke(
        rootcli.rootcli, ['auth', 'login', '--username=username', '--password=password'])

    mock_prompt.assert_called()
