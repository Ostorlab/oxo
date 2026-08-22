"""Tests for scan run risk command."""

from click import testing as click_testing
from pytest_mock import plugin

from ostorlab.cli import rootcli
from ostorlab.assets import risk, domain_name, ipv4


def testScanRunRisk_whenDomainTargetProvided_callsScanWithValidAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Test scan run risk with domain target."""
    runner = click_testing.CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=True
    )

    runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent/ostorlab/nmap",
            "risk",
            "--severity",
            "HIGH",
            "--description",
            "Open vulnerable port",
            "--domain",
            "example.com",
        ],
    )

    assert scan_mocked.call_count == 1
    assets = scan_mocked.call_args_list[0].kwargs.get("assets", [])
    assert len(assets) == 1
    asset = assets[0]
    assert isinstance(asset, risk.Risk)
    assert asset.rating == "HIGH"
    assert asset.description == "Open vulnerable port"
    assert isinstance(asset.target, domain_name.DomainName)
    assert asset.target.name == "example.com"
    assert asset.selector == "v3.asset.risk"
    assert asset.proto_field == "risk"


def testScanRunRisk_whenIpTargetProvided_callsScanWithValidAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Test scan run risk with IP target."""
    runner = click_testing.CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=True
    )

    runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent/ostorlab/nmap",
            "risk",
            "--severity",
            "MEDIUM",
            "--description",
            "IP risk",
            "--ip",
            "192.168.1.1/32",
        ],
    )

    assert scan_mocked.call_count == 1
    assets = scan_mocked.call_args_list[0].kwargs.get("assets", [])
    assert len(assets) == 1
    asset = assets[0]
    assert isinstance(asset, risk.Risk)
    assert asset.rating == "MEDIUM"
    assert isinstance(asset.target, ipv4.IPv4)
    assert asset.target.host == "192.168.1.1"
