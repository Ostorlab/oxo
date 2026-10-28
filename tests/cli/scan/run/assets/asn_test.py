"""Tests for the scan run asn command."""

from click import testing
from pytest_mock import plugin

from ostorlab.assets import asn
from ostorlab.cli import rootcli


def testScanRunASN_whenNoOptionsProvided_showsUsageAndExitsWithError(
    mocker: plugin.MockerFixture,
) -> None:
    """Test oxo scan run asn command with no arguments.
    Should show usage and exit with exit_code = 2."""
    runner = testing.CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    result = runner.invoke(
        rootcli.rootcli,
        ["scan", "run", "--agent=agent1", "asn"],
    )

    assert result.exit_code == 2
    assert "Missing argument" in result.output


def testScanRunASN_whenValidASNProvided_invokesRuntime(
    mocker: plugin.MockerFixture,
) -> None:
    """Test oxo scan run asn with a valid ASN triggers a scan."""
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    mock_scan = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )
    runner = testing.CliRunner()
    result = runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "--runtime=local",
            "run",
            "--agent=agent1",
            "asn",
            "15169",
        ],
    )

    assert mock_scan.called
    call_assets = mock_scan.call_args[1]["assets"]
    assert len(call_assets) == 1
    assert isinstance(call_assets[0], asn.ASN)
    assert call_assets[0].asn == "15169"
    assert result.exit_code == 0


def testScanRunASN_whenMultipleASNsProvided_invokesRuntimeWithAllAssets(
    mocker: plugin.MockerFixture,
) -> None:
    """Test oxo scan run asn with multiple ASNs passes all assets to runtime."""
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    mock_scan = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )
    runner = testing.CliRunner()
    result = runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "--runtime=local",
            "run",
            "--agent=agent1",
            "asn",
            "15169",
            "13335",
        ],
    )

    assert mock_scan.called
    call_assets = mock_scan.call_args[1]["assets"]
    assert [a.asn for a in call_assets] == ["15169", "13335"]
    assert all(isinstance(a, asn.ASN) for a in call_assets)
    assert all(a.selector == "v3.asset.asn" for a in call_assets)
    assert result.exit_code == 0


def testScanRunASN_whenCloudRuntime_refusesWithoutCreatingScan(
    mocker: plugin.MockerFixture,
) -> None:
    """The cloud runtime has no ASN input yet, the command fails before creating a scan."""
    mocker.patch(
        "ostorlab.runtimes.cloud.runtime.CloudRuntime.__init__", return_value=None
    )
    mocker.patch(
        "ostorlab.runtimes.cloud.runtime.CloudRuntime.can_run", return_value=True
    )
    mock_scan = mocker.patch("ostorlab.runtimes.cloud.runtime.CloudRuntime.scan")
    runner = testing.CliRunner()

    result = runner.invoke(
        rootcli.rootcli,
        ["scan", "--runtime=cloud", "run", "--agent=agent1", "asn", "15169"],
    )

    assert result.exit_code == 1
    assert "ASN scans are not supported on the cloud runtime yet." in result.output
    mock_scan.assert_not_called()
