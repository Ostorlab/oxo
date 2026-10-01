"""Runtime failures must remain visible through the real CLI entry point."""

import pathlib

import httpx
import pytest
import sqlalchemy
from click import testing
from pytest_httpx import HTTPXMock
from pytest_mock import plugin

from ostorlab import exceptions
from ostorlab.apis.runners import runner
from ostorlab.cli import rootcli
from ostorlab.runtimes.cloud import runtime as cloud_runtime
from ostorlab.runtimes.local import runtime as local_runtime


@pytest.mark.parametrize(
    "operation", ["scan", "stop", "list", "vulnz", "describe", "dump"]
)
@pytest.mark.parametrize("failure", ["http401", "graphql", "transport"])
def testCloudCLI_whenRequestFails_reportsNonzeroUsefulError(
    operation: str,
    failure: str,
    httpx_mock: HTTPXMock,
    tmp_path: pathlib.Path,
) -> None:
    """HTTP and API errors travel through runtime handlers and the root CLI."""
    if operation == "scan":
        httpx_mock.add_response(json={"data": {"agent": {}}})
        args = [
            "scan",
            "--runtime=cloud",
            "run",
            "--agent=agent/ostorlab/nmap",
            "ip",
            "8.8.8.8",
        ]
        context = "create scan"
    elif operation in ["stop", "list"]:
        args = ["scan", "--runtime=cloud", operation]
        if operation == "stop":
            args.append("123")
        context = "stop scan 123" if operation == "stop" else "fetch scans"
    else:
        command = "list" if operation == "vulnz" else operation
        args = ["vulnz", "--runtime=cloud", command, "--scan-id=123"]
        if operation == "dump":
            args += ["--output", str(tmp_path / "vulnz.jsonl")]
        context = "123"
    if failure == "http401":
        httpx_mock.add_response(status_code=401, json={"detail": "Unauthorized"})
        detail = "401"
    elif failure == "graphql":
        httpx_mock.add_response(json={"errors": [{"message": "Access denied"}]})
        detail = "Access denied"
    else:
        httpx_mock.add_exception(httpx.ConnectError("Connection refused"))
        detail = "Connection refused"

    result = testing.CliRunner().invoke(rootcli.rootcli, ["--api-key=test", *args])

    assert result.exit_code != 0
    assert "Error:" in result.output
    assert detail in result.output
    assert context in result.output
    assert "Scan created successfully" not in result.output


def testRunnerError_whenRaised_usesRepositoryErrorHierarchy() -> None:
    """API failures participate in the common runtime and CLI error contract."""
    assert isinstance(runner.ResponseError("failed"), exceptions.OstorlabError)


@pytest.mark.parametrize("outcome", [False, None, True])
def testStopCLI_whenRuntimeReturnsOutcome_acceptsOnlySuccessfulOutcome(
    outcome: object, mocker: plugin.MockerFixture
) -> None:
    """Explicit False is a failure while legacy None remains successful."""
    mocker.patch.object(local_runtime.LocalRuntime, "__init__", return_value=None)
    stop = mocker.patch.object(local_runtime.LocalRuntime, "stop", return_value=outcome)

    result = testing.CliRunner().invoke(rootcli.rootcli, ["scan", "stop", "123"])

    stop.assert_called_once_with(scan_id=123)
    assert result.exit_code == (1 if outcome is False else 0)
    if outcome is False:
        assert "Could not stop scan 123" in result.output


@pytest.mark.parametrize("command", [["list"], ["stop", "--all"], ["stop", "--last"]])
@pytest.mark.parametrize("missing", [True, False])
def testScanListCLI_whenRuntimeReturnsMissingOrEmptyList_distinguishesFailure(
    command: list[str], missing: bool, mocker: plugin.MockerFixture
) -> None:
    """A missing list is an operational failure; an empty list is valid."""
    mocker.patch.object(local_runtime.LocalRuntime, "__init__", return_value=None)
    mocker.patch.object(
        local_runtime.LocalRuntime, "list", return_value=None if missing else []
    )
    stop = mocker.patch.object(local_runtime.LocalRuntime, "stop")

    result = testing.CliRunner().invoke(rootcli.rootcli, ["scan", *command])

    assert result.exit_code == (1 if missing else 0)
    if missing:
        assert "Could not fetch scans" in result.output
    stop.assert_not_called()


def testDumpCLI_whenDatabaseFails_reportsScanAndCause(
    mocker: plugin.MockerFixture, tmp_path: pathlib.Path
) -> None:
    """Local database failures cannot be reported as successful dumps."""
    error = sqlalchemy.exc.OperationalError(
        "SELECT", {}, RuntimeError("database unavailable")
    )
    mocker.patch.object(local_runtime.LocalRuntime, "__init__", return_value=None)
    mocker.patch.object(local_runtime.LocalRuntime, "dump_vulnz", side_effect=error)

    result = testing.CliRunner().invoke(
        rootcli.rootcli,
        ["vulnz", "dump", "--scan-id=123", "--output", str(tmp_path / "vulnz.jsonl")],
    )

    assert result.exit_code == 1
    assert "123" in result.output
    assert "database unavailable" in result.output


def testRootCLI_whenUnexpectedFailureOccurs_preservesProgrammerError(
    mocker: plugin.MockerFixture,
) -> None:
    """Only expected operational errors are translated into Click errors."""
    error = RuntimeError("unexpected")
    mocker.patch.object(cloud_runtime.CloudRuntime, "list", side_effect=error)

    result = testing.CliRunner().invoke(
        rootcli.rootcli, ["scan", "--runtime=cloud", "list"]
    )

    assert result.exception is error


def testRootCLI_whenPreflightTransportFails_preservesHttpCause(
    httpx_mock: HTTPXMock,
) -> None:
    """HTTP errors outside operation handlers reach the root error translator."""
    error = httpx.ConnectError("Connection refused")
    httpx_mock.add_exception(error)

    result = testing.CliRunner().invoke(
        rootcli.rootcli,
        [
            "--api-key=test",
            "scan",
            "--runtime=cloud",
            "run",
            "--agent=agent/ostorlab/nmap",
            "ip",
            "8.8.8.8",
        ],
        standalone_mode=False,
    )

    assert result.exit_code == 1
    assert str(result.exception) == "HTTP request failed: Connection refused"
    assert result.exception.__cause__ is error
