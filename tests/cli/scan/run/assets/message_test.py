"""Tests for scan run message command."""

from click import testing

from ostorlab.assets import message as message_asset
from ostorlab.cli import rootcli


def testScanRunMessage_whenNoOptionsProvided_shouldShowUsageError(scan_run_cli_runner):
    """Test oxo scan run message command with no options.
    Should show error for missing required options."""
    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        ["scan", "run", "--agent=agent1", "message"],
    )

    assert result.exit_code == 2
    assert "Missing option" in result.output


def testScanRunMessage_whenValidSelectorAndTextprotoFile_shouldCallScanWithMessageAsset(
    scan_run_cli_runner,
    mocker,
    tmp_path,
):
    """Test oxo scan run message with valid selector and proto text file."""
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )
    proto_file = tmp_path / "risk.textproto"
    proto_file.write_text('rating: "HIGH"\ndescription: "Server exposed"')

    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "message",
            "--selector=v3.report.risk",
            f"--textproto={proto_file}",
        ],
    )

    assert result.exit_code == 0
    assert scan_mocked.call_count == 1
    assets = scan_mocked.call_args[1].get("assets")
    assert len(assets) == 1
    assert isinstance(assets[0], message_asset.Message)
    assert assets[0].selector == "v3.report.risk"
    assert len(assets[0].proto_bytes) > 0


def testScanRunMessage_whenInvalidSelector_shouldShowError(
    scan_run_cli_runner,
    tmp_path,
):
    """Test oxo scan run message with a selector that has no matching proto definition."""
    proto_file = tmp_path / "msg.textproto"
    proto_file.write_text('field: "value"')

    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "message",
            "--selector=v3.nonexistent.selector",
            f"--textproto={proto_file}",
        ],
    )

    assert result.exit_code == 2


def testScanRunMessage_whenInvalidProtoText_shouldShowError(
    scan_run_cli_runner,
    tmp_path,
):
    """Test oxo scan run message with invalid proto text content."""
    proto_file = tmp_path / "bad.textproto"
    proto_file.write_text("this is not valid proto text {{{")

    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "message",
            "--selector=v3.report.risk",
            f"--textproto={proto_file}",
        ],
    )

    assert result.exit_code == 2


def testScanRunMessage_whenFileNotFound_shouldShowError(scan_run_cli_runner):
    """Test oxo scan run message with a non-existent file path."""
    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "message",
            "--selector=v3.report.risk",
            "--textproto=/nonexistent/path/msg.textproto",
        ],
    )

    assert result.exit_code == 2


def testMessageAsset_toProto_shouldReturnPrecomputedBytes():
    """Test that Message asset returns pre-computed proto bytes."""
    proto_bytes = b"\x01\x02\x03"
    msg = message_asset.Message(selector="v3.report.risk", proto_bytes=proto_bytes)

    assert msg.to_proto() == proto_bytes


def testMessageAsset_selector_shouldReturnDynamicSelector():
    """Test that Message asset returns the dynamic selector."""
    msg = message_asset.Message(selector="v3.foo.bar", proto_bytes=b"")

    assert msg.selector == "v3.foo.bar"
