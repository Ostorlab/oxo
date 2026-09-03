"""Unit tests for the ostorlab scanner subcommand."""

import inspect
import logging
import os
import sys

import pytest
from click import testing as click_testing
from google.cloud import logging as gcp_logging
from google.cloud.logging import handlers as gcp_logging_handlers
from pytest_mock import plugin

from ostorlab.cli import rootcli
from ostorlab.cli.scanner import scanner as scanner_cli


def _remove_scanner_file_handlers() -> None:
    root_logger = logging.getLogger()
    for handler in list(root_logger.handlers):
        if getattr(handler, "name", None) == scanner_cli.SCANNER_FILE_HANDLER_NAME:
            root_logger.removeHandler(handler)
            handler.close()


def _start_scanner_sync(mocker: plugin.MockerFixture, **kwargs) -> None:
    mocker.patch("ostorlab.cli.scanner.scanner.scan_handler.start_scan_loop")

    scanner_cli.start_scanner(
        api_key=None,
        scanner_id="11226DS",
        state_reporter=mocker.Mock(),
        **kwargs,
    )


@pytest.mark.skipif(sys.platform == "win32", reason="does not run on windows")
def testScannerCommandInvocation_whenDaemonCommandIsProvided_runsBackground(
    mocker: plugin.MockerFixture,
) -> None:
    """Run CLI with daemon command."""
    daemon_context_open = mocker.patch("daemon.DaemonContext.open", return_value=None)
    mocker.patch("ostorlab.cli.scanner.scanner", return_value=None)
    runner = click_testing.CliRunner()
    runner.invoke(
        rootcli.rootcli,
        ["--api-key", "test", "scanner", "--daemon", "--scanner-id", "11226"],
    )

    assert daemon_context_open.call_count == 1


@pytest.mark.skipif(sys.platform == "win32", reason="does not run on windows")
def testScannerCommandInvocation_whenDaemonCommandIsDisabled_runsConnection(
    mocker: plugin.MockerFixture,
) -> None:
    """Run CLI with --no-daemon command."""
    mocker.patch(
        "ostorlab.cli.scanner.scanner.start_scanner",
        return_value=None,
    )
    create_scan_process_mock = mocker.patch("multiprocessing.Process")

    runner = click_testing.CliRunner()
    runner.invoke(
        rootcli.rootcli,
        ["scanner", "--no-daemon", "--scanner-id", "11226DS"],
    )

    assert create_scan_process_mock.call_count == 1


@pytest.mark.skipif(sys.platform == "win32", reason="does not run on windows")
def testScannerCommandInvocation_whenApiKeyProvided_passesItToStateReporter(
    mocker: plugin.MockerFixture,
) -> None:
    """The state reporter must authenticate RE requests with the CLI API key."""
    mocker.patch.object(scanner_cli, "_configure_file_logging")
    mocker.patch(
        "ostorlab.cli.scanner.scanner.start_scanner",
        return_value=None,
    )
    mocker.patch("multiprocessing.Process")
    state_reporter_mock = mocker.patch(
        "ostorlab.cli.scanner.scanner.scanner_state_reporter.ScannerStateReporter"
    )

    runner = click_testing.CliRunner()
    result = runner.invoke(
        rootcli.rootcli,
        [
            "--api-key",
            "reporting-engine-api-key",
            "scanner",
            "--no-daemon",
            "--scanner-id",
            "11226DS",
        ],
    )

    assert result.exit_code == 0
    state_reporter_mock.assert_called_once_with(
        scanner_id="11226DS",
        hostname=mocker.ANY,
        ip=mocker.ANY,
        reporting_engine_api_key="reporting-engine-api-key",
    )


@pytest.mark.skipif(sys.platform == "win32", reason="does not run on windows")
def testScannerCommandInvocation_whenGcpCredentialProvided_forwardsItToProcess(
    mocker: plugin.MockerFixture,
) -> None:
    """Forward GCP logging credentials to every scanner process."""
    mocker.patch.object(scanner_cli, "_configure_file_logging")
    create_process_mock = mocker.patch("multiprocessing.Process")
    mocker.patch(
        "ostorlab.cli.rootcli.open",
        mocker.mock_open(read_data='{"project_id": "test-project"}'),
    )
    mocker.patch("google.oauth2.service_account.Credentials.from_service_account_info")
    mocker.patch("google.cloud.logging.Client")

    runner = click_testing.CliRunner()
    result = runner.invoke(
        rootcli.rootcli,
        [
            "--gcp-logging-credential",
            __file__,
            "scanner",
            "--no-daemon",
            "--scanner-id",
            "11226DS",
        ],
    )

    assert result.exit_code == 0
    process_args = create_process_mock.call_args.kwargs["args"]
    assert process_args[5] == '{"project_id": "test-project"}'


@pytest.mark.skipif(sys.platform == "win32", reason="does not run on windows")
def testScannerCommandInvocation_whenParallelScanNumberIsGiven_shouldCreateCorrespondingProcesses(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure the correct number of scan processes are created."""
    create_process_mock = mocker.patch("multiprocessing.Process")

    runner = click_testing.CliRunner()
    runner.invoke(
        rootcli.rootcli,
        ["scanner", "--no-daemon", "--scanner-id", "11226DS", "--parallel", 42],
    )

    assert create_process_mock.call_count == 42


@pytest.mark.skipif(sys.platform == "win32", reason="does not run on windows")
def testScannerCommandInvocation_whenParallelScanNumberIsNegative_shouldExistAndShowHelpMessage(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure scanner sub-command handles the case where the number of parallel scans is negative."""
    create_process_mock = mocker.patch("multiprocessing.Process")

    runner = click_testing.CliRunner()
    result = runner.invoke(
        rootcli.rootcli,
        ["scanner", "--no-daemon", "--scanner-id", "11226DS", "--parallel", -42],
    )

    assert create_process_mock.call_count == 0
    assert result.exit_code == 2
    assert (
        "Invalid value for '--parallel': -42 is not in the range x>=1" in result.output
    )


def testConfigureFileLogging_whenLogFileIsProvided_persistsLogs(
    mocker: plugin.MockerFixture,
    tmp_path,
) -> None:
    """Ensure scanner logs can be persisted to a file."""
    _remove_scanner_file_handlers()
    root_logger = logging.getLogger()
    original_level = root_logger.level
    log_file = tmp_path / "scanner.log"

    try:
        _start_scanner_sync(mocker, log_file=str(log_file))
        logging.getLogger().info("scanner log message")
    finally:
        _remove_scanner_file_handlers()
        root_logger.setLevel(original_level)

    assert "scanner log message" in log_file.read_text()


def testConfigureFileLogging_whenDebugLevelIsProvided_persistsDebugLogs(
    mocker: plugin.MockerFixture,
    tmp_path,
) -> None:
    """Ensure scanner file logs honor the configured log level."""
    _remove_scanner_file_handlers()
    root_logger = logging.getLogger()
    original_level = root_logger.level
    log_file = tmp_path / "scanner.log"

    try:
        root_logger.setLevel(logging.ERROR)
        _start_scanner_sync(mocker, log_file=str(log_file), log_level=logging.DEBUG)
        logging.getLogger().debug("scanner debug log message")
    finally:
        _remove_scanner_file_handlers()
        root_logger.setLevel(original_level)

    assert "scanner debug log message" in log_file.read_text()


@pytest.mark.skipif(sys.platform == "win32", reason="does not run on windows")
def testScannerCommandInvocation_whenPersistLogsIsProvided_passesLogFileToWorker(
    mocker: plugin.MockerFixture,
    tmp_path,
) -> None:
    """Ensure persisted log file path is passed to scanner workers."""
    _remove_scanner_file_handlers()
    create_scan_process_mock = mocker.patch("multiprocessing.Process")
    log_file = tmp_path / "scanner.log"

    runner = click_testing.CliRunner()
    try:
        result = runner.invoke(
            rootcli.rootcli,
            [
                "scanner",
                "--no-daemon",
                "--scanner-id",
                "11226DS",
                "--persist-logs",
                "--log-file",
                str(log_file),
            ],
        )
    finally:
        _remove_scanner_file_handlers()

    assert result.exit_code == 0
    assert create_scan_process_mock.call_count == 1
    _, _, _, scanner_log_file, scanner_log_level, _, _ = (
        create_scan_process_mock.call_args.kwargs["args"]
    )
    assert scanner_log_file == str(log_file)
    assert scanner_log_level == logging.INFO


@pytest.mark.skipif(sys.platform == "win32", reason="does not run on windows")
def testScannerCommandInvocation_whenLogLevelIsProvided_passesLogLevelToWorker(
    mocker: plugin.MockerFixture,
    tmp_path,
) -> None:
    """Ensure persisted scanner logs use the requested verbosity."""
    _remove_scanner_file_handlers()
    create_scan_process_mock = mocker.patch("multiprocessing.Process")
    log_file = tmp_path / "scanner.log"

    runner = click_testing.CliRunner()
    try:
        result = runner.invoke(
            rootcli.rootcli,
            [
                "scanner",
                "--no-daemon",
                "--scanner-id",
                "11226DS",
                "--persist-logs",
                "--log-file",
                str(log_file),
                "--log-level",
                "DEBUG",
            ],
        )
    finally:
        _remove_scanner_file_handlers()

    assert result.exit_code == 0
    assert create_scan_process_mock.call_count == 1
    _, _, _, scanner_log_file, scanner_log_level, _, _ = (
        create_scan_process_mock.call_args.kwargs["args"]
    )
    assert scanner_log_file == str(log_file)
    assert scanner_log_level == logging.DEBUG


@pytest.mark.skipif(sys.platform == "win32", reason="does not run on windows")
def testStartScanner_whenGcpCredentialProvided_setsUpLabeledCloudLoggingInWorker(
    mocker: plugin.MockerFixture,
) -> None:
    """The worker process must set up its own Cloud Logging handler since the parent's does not survive the fork."""
    mocker.patch("google.oauth2.service_account.Credentials.from_service_account_info")
    client_mock = mocker.patch("google.cloud.logging.Client")

    _start_scanner_sync(mocker, gcp_logging_credential='{"project_id": "test-project"}')

    setup_logging_mock = client_mock.return_value.setup_logging
    assert setup_logging_mock.call_count == 1
    labels = setup_logging_mock.call_args.kwargs["labels"]
    assert labels["scanner_id"] == "11226DS"
    assert labels["pid"] == str(os.getpid())
    assert client_mock.call_args.kwargs["_use_grpc"] is False


@pytest.mark.skipif(sys.platform == "win32", reason="does not run on windows")
def testStartScanner_whenNoGcpCredential_doesNotSetUpCloudLogging(
    mocker: plugin.MockerFixture,
) -> None:
    """No Cloud Logging setup should happen when no credential is passed down to the worker."""
    client_mock = mocker.patch("google.cloud.logging.Client")

    _start_scanner_sync(mocker, gcp_logging_credential=None)

    assert client_mock.call_count == 0


@pytest.mark.skipif(sys.platform == "win32", reason="does not run on windows")
def testStartScanner_whenInheritedCloudLoggingHandlerExists_removesItBeforeSetup(
    mocker: plugin.MockerFixture,
) -> None:
    """The handler inherited from the forked parent has a dead transport and must be dropped."""
    mocker.patch("google.oauth2.service_account.Credentials.from_service_account_info")
    mocker.patch("google.cloud.logging.Client")
    inherited_handler = gcp_logging_handlers.CloudLoggingHandler(
        mocker.Mock(), transport=mocker.Mock()
    )
    root_logger = logging.getLogger()
    root_logger.addHandler(inherited_handler)

    try:
        _start_scanner_sync(
            mocker, gcp_logging_credential='{"project_id": "test-project"}'
        )
    finally:
        root_logger.removeHandler(inherited_handler)

    assert inherited_handler not in root_logger.handlers


@pytest.mark.skipif(sys.platform == "win32", reason="does not run on windows")
def testStartScanner_whenGcpCredentialIsMalformed_doesNotCrashWorker(
    mocker: plugin.MockerFixture,
) -> None:
    """A bad credential must not kill the worker process before the scan loop starts."""
    start_scan_loop_mock = mocker.patch(
        "ostorlab.cli.scanner.scanner.scan_handler.start_scan_loop"
    )

    scanner_cli.start_scanner(
        api_key=None,
        scanner_id="11226DS",
        state_reporter=mocker.Mock(),
        gcp_logging_credential="not-json",
    )

    assert start_scan_loop_mock.call_count == 1


@pytest.mark.skipif(sys.platform == "win32", reason="does not run on windows")
def testCloudLoggingClient_always_acceptsDisablingGrpcTransport() -> None:
    """Workers disable the fork-unsafe gRPC transport through a private parameter of the client.

    The client is mocked in the tests above, so a mock would happily accept a parameter the library no longer
    supports. Assert against the real signature instead, to fail on upgrade rather than silently dropping logs.
    """
    parameters = inspect.signature(gcp_logging.Client.__init__).parameters

    assert "_use_grpc" in parameters
