"""Tests for auth login command."""
from click.testing import CliRunner
from ostorlab.cli import rootcli
from ostorlab.apis import runner as apis_runner
from ostorlab.apis import request as api_request

import click
from unittest import mock


def testOstorlabAuthLoginCLI_whenNoOptionsProvided_showsAvailableOptionsAndCommands():
    """Test ostorlab auth login command with no options. Should usage."""

    runner = CliRunner()
    result = runner.invoke(rootcli.rootcli, ['auth', 'login'])
    assert 'Usage: rootcli auth login [OPTIONS]' in result.output
    assert result.exit_code == 2


@mock.patch.object(apis_runner.AuthenticationError, '__init__')
def testOstorlabAuthLoginCLI_whenInvalidLoginCredentialsAreProvided_raisesAuthenticationException(mock___init__, requests_mock):
    """Test ostorlab auth login command with wrong login credentials.
    Should assert that the AuthenticationError is raised.
    """
    runner = CliRunner()
    requests_mock.post(api_request.TOKEN_ENDPOINT, json={'non_field_errors': [
                       'Unable to log in with provided credentials.']}, status_code=400)
    runner.invoke(
        rootcli.rootcli, ['auth', 'login', '--username=username', '--password=password'])
    mock___init__.assert_called()


def testOstorlabAuthLoginCLI_whenValidLoginCredentialsAreProvided_setsToken(requests_mock):
    runner = CliRunner()
    requests_mock.post(api_request.TOKEN_ENDPOINT, [
                       {'json': {'token': '2fd7a589-64b4-442e-95aa-eb0d082aab63'}, 'status_code': 200}])
    result = runner.invoke(
        rootcli.rootcli, ['auth', 'login', '--username=username', '--password=password'])
    assert result.exception is None


@ mock.patch.object(click, 'prompt')
def testOstorlabAuthLoginCLI_whenValidLoginCredentialsAreProvidedWithoutOtp_promptOtp(mock_prompt, requests_mock):
    """Test ostorlab auth login command with correct login credentials without OTP.
    Should assert that the otp prompt is called.
    """
    mock_prompt.return_value = None
    runner = CliRunner()
    requests_mock.post(api_request.TOKEN_ENDPOINT, json={'non_field_errors': [
                       'Must include "otp_token"']}, status_code=400)
    runner.invoke(
        rootcli.rootcli, ['auth', 'login', '--username=username', '--password=password'])
    mock_prompt.assert_called()
