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


@pytest.mark.parametrize("empty_errors", [True, False])
def testCloudStopCLI_whenHttpResponseSuccessful_reportsSuccess(
    empty_errors: bool, httpx_mock: HTTPXMock
) -> None:
    """Successful HTTP responses permit absent or empty GraphQL errors."""
    httpx_mock.add_response(
        json={
            "data": {"stopScan": {"scan": {"id": 123}}},
            **({"errors": []} if empty_errors is True else {}),
        }
    )

    result = testing.CliRunner().invoke(
        rootcli.rootcli, ["--api-key=test", "scan", "--runtime=cloud", "stop", "123"]
    )

    assert result.exit_code == 0
    assert "Scan stopped successfully" in result.output


def testCloudStopCLI_whenHttpResponseHasErrors_preservesContextAndCause(
    httpx_mock: HTTPXMock,
) -> None:
    """The runner's HTTP error is wrapped once with scan context."""
    httpx_mock.add_response(json={"errors": [{"message": "Access denied"}]})

    result = testing.CliRunner().invoke(
        rootcli.rootcli,
        ["--api-key=test", "scan", "--runtime=cloud", "stop", "123"],
        standalone_mode=False,
    )

    assert result.exit_code == 1
    assert "Could not stop scan 123: Response errors: Access denied" in str(
        result.exception
    )
    assert result.exception is not None
    contextual_error = result.exception.__cause__
    assert isinstance(contextual_error, runner.ResponseError)
    assert isinstance(contextual_error.__cause__, runner.ResponseError)
    assert str(contextual_error.__cause__) == "Response errors: Access denied"
    assert "stopped successfully" not in result.output


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
