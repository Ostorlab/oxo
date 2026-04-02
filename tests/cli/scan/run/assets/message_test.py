"""Tests for scan run message command."""

import pathlib

from click import testing
from pytest_mock import plugin

from ostorlab.assets import message as message_asset
from ostorlab.cli import rootcli


def testScanRunMessage_whenNoOptionsProvided_shouldShowUsageError(
    scan_run_cli_runner: testing.CliRunner,
) -> None:
    """Test oxo scan run message command with no options.
    Should show error for missing required options."""
    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        ["scan", "run", "--agent=agent1", "message"],
    )

    assert result.exit_code == 2
    assert "Missing option" in result.output


def testScanRunMessage_whenValidSelectorAndTextprotoFile_shouldCallScanWithMessageAsset(
    scan_run_cli_runner: testing.CliRunner,
    mocker: plugin.MockerFixture,
    tmp_path: pathlib.Path,
) -> None:
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
    scan_run_cli_runner: testing.CliRunner,
    tmp_path: pathlib.Path,
) -> None:
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
    scan_run_cli_runner: testing.CliRunner,
    tmp_path: pathlib.Path,
) -> None:
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


def testScanRunMessage_whenFileNotFound_shouldShowError(
    scan_run_cli_runner: testing.CliRunner,
) -> None:
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


def testScanRunMessage_whenTextprotoContainsBytesField_shouldCallScanWithMessageAsset(
    scan_run_cli_runner: testing.CliRunner,
    mocker: plugin.MockerFixture,
    tmp_path: pathlib.Path,
) -> None:
    """Test oxo scan run message correctly handles a proto with a bytes-type field."""
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )
    proto_file = tmp_path / "artifact.textproto"
    proto_file.write_text('content: "binary_content"\ndescription: "test artifact"')

    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "message",
            "--selector=v3.capture.artifact",
            f"--textproto={proto_file}",
        ],
    )

    assert result.exit_code == 0
    assert scan_mocked.call_count == 1
    assets = scan_mocked.call_args[1].get("assets")
    assert len(assets) == 1
    assert isinstance(assets[0], message_asset.Message)
    assert assets[0].selector == "v3.capture.artifact"
    assert len(assets[0].proto_bytes) > 0


def testMessageAsset_toProto_shouldReturnPrecomputedBytes() -> None:
    """Test that Message asset returns pre-computed proto bytes."""
    proto_bytes = b"\x01\x02\x03"
    msg = message_asset.Message(selector="v3.report.risk", proto_bytes=proto_bytes)

    assert msg.to_proto() == proto_bytes


def testMessageAsset_selector_shouldReturnDynamicSelector() -> None:
    """Test that Message asset returns the dynamic selector."""
    msg = message_asset.Message(selector="v3.foo.bar", proto_bytes=b"")

    assert msg.selector == "v3.foo.bar"
