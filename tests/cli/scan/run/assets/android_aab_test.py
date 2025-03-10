"""Tests for scan run android-aab command."""

from unittest import mock

from click.testing import CliRunner
from pytest_mock import plugin

from ostorlab.cli import rootcli
from ostorlab import exceptions


def testScanRunAndroidAab_whenNoOptionsProvided_shouldExitAndShowError(mocker):
    """Test oxo scan run android-aab command with no options and no sub command.
    Should show error message and exit with exit_code = 2."""

    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    result = runner.invoke(
        rootcli.rootcli, ["scan", "run", "--agent=agent1 --agent=agent2", "android-aab"]
    )

    assert (
        "Command missing either file path or source url of the aab file."
        in result.output
    )
    assert result.exit_code == 2


def testScanRunAndroidAab_whenBothFileAndUrlOptionsAreProvided_shouldExitAndShowError(
    mocker,
):
    """Test oxo scan run android-aab command when both file & url options are provided.
    Should show error message and exit with exit_code = 2."""

    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    command = [
        "scan",
        "run",
        "--agent=agent1",
        "android-aab",
        "--file",
        "tests/__init__.py",
        "--url",
        "url1",
    ]
    result = runner.invoke(rootcli.rootcli, command)

    assert result.exit_code == 2


@mock.patch("ostorlab.cli.scan.run.assets.common.download_file")
def testScanRunAndroidAab_whenUrlIsProvided_callsDownloadFile(
    mock_download_file: mock.MagicMock,
    mocker: plugin.MockerFixture,
) -> None:
    """Test oxo scan run android-aab command when URL option is provided.
    Should download the file and create an AndroidAab asset with the downloaded content."""

    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.runtime.LocalRuntime.scan")
    mocker.patch("ostorlab.runtimes.local.runtime.LocalRuntime.link_agent_group_scan")
    mocker.patch("ostorlab.runtimes.local.runtime.LocalRuntime.link_assets_scan")
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    mock_download_file.return_value = b"downloaded content"
    test_url = "https://example.com/test.aab"

    result = runner.invoke(
        rootcli.rootcli,
        ["scan", "run", "--agent=agent1", "android-aab", "--url", test_url],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    mock_download_file.assert_called_once()
    assert "Downloading file from" in result.output
    assert "File downloaded successfully" in result.output


@mock.patch("ostorlab.cli.scan.run.assets.common.download_file")
def testScanRunAndroidAab_whenDownloadFails_shouldExitWithError(
    mock_download_file: mock.MagicMock,
    mocker: plugin.MockerFixture,
) -> None:
    """Test oxo scan run android-aab command when file download fails.
    Should show error and exit with code 2."""

    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    mock_download_file.side_effect = exceptions.OstorlabError("Download failed")
    test_url = "https://example.com/test.aab"

    result = runner.invoke(
        rootcli.rootcli,
        ["scan", "run", "--agent=agent1", "android-aab", "--url", test_url],
    )

    assert result.exit_code == 2
    mock_download_file.assert_called_once()
    assert "Download failed" in result.output
