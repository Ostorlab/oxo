"""Tests for scan run ios-ipa command."""

import requests
from click.testing import CliRunner
from pytest_mock import plugin

from ostorlab.cli import rootcli


def testScanRunIosIpa_whenNoOptionsProvided_shouldExitAndShowError(mocker):
    """Test oxo scan run ios-ipa command with no options and no sub command.
    Should show error message and exit with exit_code = 2."""

    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    result = runner.invoke(
        rootcli.rootcli, ["scan", "run", "--agent=agent1 --agent=agent2", "ios-ipa"]
    )

    assert (
        "Command missing either file path or source url of the ipa file."
        in result.output
    )
    assert result.exit_code == 2


def testScanRunIosIpa_whenBothFileAndUrlOptionsAreProvided_shouldExitAndShowError(
    mocker,
):
    """Test oxo scan run ios-ipa command when both file & url options are provided.
    Should show error message and exit with exit_code = 2."""

    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    command = [
        "scan",
        "run",
        "--agent=agent1",
        "ios-ipa",
        "--file",
        "tests/__init__.py",
        "--url",
        "url1",
    ]
    result = runner.invoke(rootcli.rootcli, command)

    assert result.exit_code == 2


def testScanRunIosIpa_whenUrlIsProvided_callsDownloadFile(
    mocker: plugin.MockerFixture,
) -> None:
    """Test oxo scan run ios-ipa command when URL option is provided.
    Should download the file and create an IOSIpa asset with the downloaded content."""

    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.runtime.LocalRuntime.scan")
    mocker.patch("ostorlab.runtimes.local.runtime.LocalRuntime.link_agent_group_scan")
    mocker.patch("ostorlab.runtimes.local.runtime.LocalRuntime.link_assets_scan")
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    test_url = "https://example.com/test.ipa"
    mock_response = mocker.Mock()
    mock_response.content = b"test content"
    mock_get = mocker.patch("requests.get", return_value=mock_response)

    result = runner.invoke(
        rootcli.rootcli,
        ["scan", "run", "--agent=agent1", "ios-ipa", "--url", test_url],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    mock_get.assert_called_once()
    assert "Downloading file from" in result.output
    assert "File downloaded successfully" in result.output


def testScanRunIosIpa_whenDownloadFails_shouldExitWithError(
    mocker: plugin.MockerFixture,
) -> None:
    """Test oxo scan run ios-ipa command when file download fails.
    Should show error and exit with code 2."""

    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    test_url = "https://example.com/test.ipa"
    mock_get = mocker.patch(
        "requests.get",
        side_effect=requests.exceptions.RequestException("Connection error"),
    )

    result = runner.invoke(
        rootcli.rootcli,
        ["scan", "run", "--agent=agent1", "ios-ipa", "--url", test_url],
    )

    assert result.exit_code == 2
    mock_get.assert_called_once()
    assert "Failed to download file" in result.output
