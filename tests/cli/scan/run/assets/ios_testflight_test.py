"""Tests for scan runs ios_testflight command."""

from click.testing import CliRunner
from pytest_mock import plugin

from ostorlab.cli import rootcli


def testScanRunIOSTestflight_whenNoOptionsProvided_shouldExitAndShowError(
    mocker: plugin.MockerFixture,
) -> None:
    """Test oxo scan run ios-testflight command with neither an application url nor an app name.
    Should show error message and exit with exit_code = 2."""

    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    result = runner.invoke(
        rootcli.rootcli,
        ["scan", "run", "--agent=agent1 --agent=agent2", "ios-testflight"],
    )

    assert "Command missing a testflight application url or app name." in result.output
    assert result.exit_code == 2


def testScanRunIOSTestflight_whenAppNameProvided_shouldRunScanWithPrivateTestflightAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Test oxo scan run ios-testflight command with the name of a private TestFlight app."""
    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    scan_mock = mocker.patch("ostorlab.runtimes.local.LocalRuntime.scan")

    runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1 --agent=agent2",
            "ios-testflight",
            "--app-name",
            "Guest + Uat",
        ],
    )

    asset = scan_mock.call_args.kwargs["assets"][0]
    assert asset.application_url is None
    assert asset.app_name == "Guest + Uat"
