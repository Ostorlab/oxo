"""Tests for scan run risk command."""

from click import testing

from ostorlab.cli import rootcli
from ostorlab.assets import risk as risk_asset


def testScanRunRisk_whenNoOptionsProvided_shouldShowUsageError(scan_run_cli_runner):
    """Test oxo scan run risk command with no options.
    Should show error for missing required options."""
    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        ["scan", "run", "--agent=agent1", "risk"],
    )

    assert result.exit_code == 2
    assert "Missing option" in result.output


def testScanRunRisk_whenValidSeverityAndDescription_shouldCallScanWithRiskAsset(
    scan_run_cli_runner,
    mocker,
):
    """Test oxo scan run risk command with severity and description."""
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )

    result = scan_run_cli_runner.invoke(
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


def testScanRunRisk_whenIpProvided_shouldCallScanWithRiskAssetContainingIp(
    scan_run_cli_runner,
    mocker,
):
    """Test oxo scan run risk command with --ip flag populates ipv4 field."""
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )

    result = scan_run_cli_runner.invoke(
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


def testScanRunRisk_whenDomainProvided_shouldCallScanWithRiskAssetContainingDomain(
    scan_run_cli_runner,
    mocker,
):
    """Test oxo scan run risk command with --domain flag populates domain_name field."""
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )

    result = scan_run_cli_runner.invoke(
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


def testScanRunRisk_whenLinkProvided_shouldCallScanWithRiskAssetContainingLink(
    scan_run_cli_runner,
    mocker,
):
    """Test oxo scan run risk command with --link flag populates link field."""
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )

    result = scan_run_cli_runner.invoke(
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


def testScanRunRisk_whenRuntimeCannotRun_shouldExitWithError(mocker):
    """Test oxo scan run risk when runtime cannot run the agents."""
    runner = testing.CliRunner()
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


def testScanRunRisk_whenDescriptionFileProvided_shouldReadFromFile(
    scan_run_cli_runner,
    mocker,
    tmp_path,
):
    """Test oxo scan run risk command with --description-file reads description from file."""
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )
    desc_file = tmp_path / "description.txt"
    desc_file.write_text("Detailed risk description from file")

    result = scan_run_cli_runner.invoke(
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


def testScanRunRisk_whenBothDescriptionAndFile_shouldShowError(
    scan_run_cli_runner,
    tmp_path,
):
    """Test oxo scan run risk with both --description and --description-file shows error."""
    desc_file = tmp_path / "description.txt"
    desc_file.write_text("File content")

    result = scan_run_cli_runner.invoke(
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


def testScanRunRisk_whenNeitherDescriptionNorFile_shouldShowError(
    scan_run_cli_runner,
):
    """Test oxo scan run risk with neither --description nor --description-file shows error."""
    result = scan_run_cli_runner.invoke(
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


def testRiskAsset_serialization_shouldProduceValidProtobuf():
    """Test that Risk asset serializes to valid protobuf bytes."""
    r = risk_asset.Risk(description="test risk", rating="HIGH")
    proto_bytes = r.to_proto()

    assert isinstance(proto_bytes, bytes)
    assert len(proto_bytes) > 0


def testRiskAsset_serializationWithIp_shouldProduceValidProtobuf():
    """Test that Risk asset with embedded IP serializes correctly."""
    r = risk_asset.Risk(
        description="server exposed",
        rating="CRITICAL",
        ipv4={"host": "8.8.8.8", "mask": "32", "version": 4},
    )
    proto_bytes = r.to_proto()

    assert isinstance(proto_bytes, bytes)
    assert len(proto_bytes) > 0


def testRiskAsset_selector_shouldBeCorrect():
    """Test that Risk asset has the correct selector."""
    r = risk_asset.Risk(description="test", rating="HIGH")
    assert r.selector == "v3.report.risk"
