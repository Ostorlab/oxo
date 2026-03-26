"""Tests for scan run risk command."""

from click.testing import CliRunner
from pytest_mock import plugin

from ostorlab.cli import rootcli
from ostorlab.assets import risk as risk_asset


def testScanRunRisk_whenNoOptionsProvided_showsUsageError(mocker):
    """Test oxo scan run risk command with no options.
    Should show error for missing required options."""
    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    result = runner.invoke(
        rootcli.rootcli,
        ["scan", "run", "--agent=agent1", "risk"],
    )

    assert result.exit_code == 2
    assert "Missing option" in result.output


def testScanRunRisk_whenValidSeverityAndDescription_callsScanWithRiskAsset(mocker):
    """Test oxo scan run risk command with severity and description."""
    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )

    result = runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "risk",
            "--severity=HIGH",
            "--description=Server exposed to internet",
        ],
    )

    assert result.exit_code == 0
    assert scan_mocked.call_count == 1
    assets = scan_mocked.call_args[1].get("assets")
    assert len(assets) == 1
    assert isinstance(assets[0], risk_asset.Risk)
    assert assets[0].rating == "HIGH"
    assert assets[0].description == "Server exposed to internet"


def testScanRunRisk_whenIpProvided_callsScanWithRiskAssetContainingIp(mocker):
    """Test oxo scan run risk command with --ip flag populates ipv4 field."""
    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )

    result = runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "risk",
            "--severity=CRITICAL",
            "--description=Test risk",
            "--ip=8.8.8.8",
        ],
    )

    assert result.exit_code == 0
    assert scan_mocked.call_count == 1
    assets = scan_mocked.call_args[1].get("assets")
    assert len(assets) == 1
    assert isinstance(assets[0], risk_asset.Risk)
    assert assets[0].ipv4 == {"host": "8.8.8.8", "mask": "32", "version": 4}


def testScanRunRisk_whenDomainProvided_callsScanWithRiskAssetContainingDomain(mocker):
    """Test oxo scan run risk command with --domain flag populates domain_name field."""
    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )

    result = runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "risk",
            "--severity=MEDIUM",
            "--description=Weak TLS",
            "--domain=example.com",
        ],
    )

    assert result.exit_code == 0
    assert scan_mocked.call_count == 1
    assets = scan_mocked.call_args[1].get("assets")
    assert len(assets) == 1
    assert isinstance(assets[0], risk_asset.Risk)
    assert assets[0].domain_name == {"name": "example.com"}


def testScanRunRisk_whenLinkProvided_callsScanWithRiskAssetContainingLink(mocker):
    """Test oxo scan run risk command with --link flag populates link field."""
    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )

    result = runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "risk",
            "--severity=LOW",
            "--description=Test link risk",
            "--link=https://example.com",
        ],
    )

    assert result.exit_code == 0
    assert scan_mocked.call_count == 1
    assets = scan_mocked.call_args[1].get("assets")
    assert len(assets) == 1
    assert isinstance(assets[0], risk_asset.Risk)
    assert assets[0].link == {"url": "https://example.com", "method": "GET"}


def testScanRunRisk_whenRuntimeCannotRun_exitsWithError(mocker):
    """Test oxo scan run risk when runtime cannot run the agents."""
    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.can_run", return_value=False
    )

    result = runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "--runtime=local",
            "run",
            "--agent=agent1",
            "risk",
            "--severity=HIGH",
            "--description=Test",
        ],
    )

    assert result.exit_code == 1


def testScanRunRisk_whenDescriptionFileProvided_readsFromFile(mocker, tmp_path):
    """Test oxo scan run risk command with --description-file reads description from file."""
    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )
    desc_file = tmp_path / "description.txt"
    desc_file.write_text("Detailed risk description from file")

    result = runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "risk",
            "--severity=HIGH",
            f"--description-file={desc_file}",
        ],
    )

    assert result.exit_code == 0
    assert scan_mocked.call_count == 1
    assets = scan_mocked.call_args[1].get("assets")
    assert len(assets) == 1
    assert assets[0].description == "Detailed risk description from file"


def testScanRunRisk_whenBothDescriptionAndFile_showsError(mocker, tmp_path):
    """Test oxo scan run risk with both --description and --description-file shows error."""
    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    desc_file = tmp_path / "description.txt"
    desc_file.write_text("File content")

    result = runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "risk",
            "--severity=HIGH",
            "--description=Inline",
            f"--description-file={desc_file}",
        ],
    )

    assert result.exit_code == 2


def testScanRunRisk_whenNeitherDescriptionNorFile_showsError(mocker):
    """Test oxo scan run risk with neither --description nor --description-file shows error."""
    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)

    result = runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "risk",
            "--severity=HIGH",
        ],
    )

    assert result.exit_code == 2


def testRiskAsset_serialization_producesValidProtobuf():
    """Test that Risk asset serializes to valid protobuf bytes."""
    r = risk_asset.Risk(description="test risk", rating="HIGH")
    proto_bytes = r.to_proto()

    assert isinstance(proto_bytes, bytes)
    assert len(proto_bytes) > 0


def testRiskAsset_serializationWithIp_producesValidProtobuf():
    """Test that Risk asset with embedded IP serializes correctly."""
    r = risk_asset.Risk(
        description="server exposed",
        rating="CRITICAL",
        ipv4={"host": "8.8.8.8", "mask": "32", "version": 4},
    )
    proto_bytes = r.to_proto()

    assert isinstance(proto_bytes, bytes)
    assert len(proto_bytes) > 0


def testRiskAsset_selector_isCorrect():
    """Test that Risk asset has the correct selector."""
    r = risk_asset.Risk(description="test", rating="HIGH")
    assert r.selector == "v3.report.risk"
