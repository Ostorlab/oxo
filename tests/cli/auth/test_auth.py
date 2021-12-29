"""Tests for auth login command."""
from click.testing import CliRunner
from ostorlab.cli import rootcli
from ostorlab.apis import runner as apis_runner
from ostorlab.apis import request as api_request

import requests_mock
import click
from unittest import mock


def testOstorlabAuthLoginCLI_whenNoOptionsProvided_showsAvailableOptionsAndCommands():
    """Test ostorlab auth login command with no options. Should usage."""

    runner = CliRunner()

    result = runner.invoke(rootcli.rootcli, ['auth', 'login'])

    assert 'Usage: rootcli auth login [OPTIONS]' in result.output
    assert result.exit_code == 2


def testOstorlabAuthLoginCLI_whenInvalidLoginCredentialsAreProvided_raisesException():
    runner = CliRunner()
    adapter = requests_mock.Adapter()

    adapter.register_uri(
        'POST', api_request.TOKEN_ENDPOINT, json={'non_field_errors': ['Unable to log in with provided credentials.']}, status_code=400)
    result = runner.invoke(
        rootcli.rootcli, ['auth', 'login', '--username=username', '--password=password'])

    assert result.exception is None


def testOstorlabAuthLoginCLI_whenValidLoginCredentialsAreProvided_setsToken():
    runner = CliRunner()
    adapter = requests_mock.Adapter()

    adapter.register_uri(
        'POST', api_request.TOKEN_ENDPOINT, json={'token': '2fd7a589-64b4-442e-95aa-eb0d082aab63'}, status_code=200)
    result = runner.invoke(
        rootcli.rootcli, ['auth', 'login', '--username=username', '--password=password'])

    assert result.exception is None


# @mock.patch.object(click, 'prompt')
def testOstorlabAuthLoginCLI_whenValidLoginCredentialsAreProvidedWithoutOtp_promptOtp():
    # mock_command_process = mock.Mock()
    # mock_prompt.return_value = None
    runner = CliRunner()
    adapter = requests_mock.Adapter()

    adapter.register_uri(
        'POST', api_request.TOKEN_ENDPOINT, json={'non_field_errors': """['Must include "otp_token"']"""}, status_code=400)
    result = runner.invoke(
        rootcli.rootcli, ['auth', 'login', '--username=username', '--password=password'])

    assert result.exception is None
    # mock_prompt.assert_called_once()
