"""Testing module for the scanner state reporter class."""

import pytest_mock

from ostorlab.utils import scanner_state_reporter
from ostorlab.utils.definitions import ScannerState


class Memory:
    percent: float = 10
    total: int = 33454317568


class Disk:
    percent: float = 50.0
    total: int = 107374182400  # 100 GB in bytes


def testReportMethod_whenCalled_updateValuesCorrectly(
    mocker: pytest_mock.MockerFixture,
) -> None:
    """Test the report method to ensure that the values filled from the private capture_state method are correct."""
    runner_mock = mocker.patch(
        "ostorlab.apis.runners.authenticated_runner.AuthenticatedAPIRunner"
    )
    mocker.patch("psutil.cpu_percent", return_value=10)
    mocker.patch("psutil.cpu_count", return_value=10)
    mocker.patch("psutil.virtual_memory", return_value=Memory())
    mocker.patch("psutil.disk_usage", return_value=Disk())
    api_request_mock = mocker.patch(
        "ostorlab.apis.add_scanner_state.AddScannerStateAPIRequest"
    )
    state = ScannerState(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        scan_id=1,
        cpu_load=10,
        total_cpu=10,
        memory_load=10,
        total_memory=31,
        hostname="",
        ip="",
        disk_usage=50.0,
        total_disk=100,
    )
    report = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="",
        ip="",
        reporting_engine_api_key="reporting-engine-api-key",
    )
    report.scan_id = 1
    report.errors = ""

    report.report()

    runner_mock.assert_called_once_with(api_key="reporting-engine-api-key")
    runner_mock.return_value.execute.assert_called_once()
    assert api_request_mock.call_args.kwargs["state"] == state


def testScannerIdProperty_whenAccessed_returnsConstructorValue() -> None:
    """The scanner_id property should expose the value passed at construction."""
    report = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD", hostname="", ip=""
    )

    assert report.scanner_id == "GGBD-DJJD-DKJK-DJDD"
