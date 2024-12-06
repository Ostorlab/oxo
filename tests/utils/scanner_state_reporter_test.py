"""Testing module for the scanner state reporter class."""

import pytest
import pytest_mock

from ostorlab.utils import scanner_state_reporter
from ostorlab.utils.definitions import ScannerState


class Memory:
    percent: float = 10
    total: int = 33454317568


@pytest.mark.asyncio
async def testReportMethod_whenCalled_updateValuesCorrectly(
    mocker: pytest_mock.MockerFixture,
) -> None:
    """Test the report method to ensure that the values filled from the private capture_state method are correct."""
    mocker.patch(
        "ostorlab.apis.runners.authenticated_runner.AuthenticatedAPIRunner.execute"
    )
    mocker.patch("psutil.cpu_percent", return_value=10)
    mocker.patch("psutil.cpu_count", return_value=10)
    mocker.patch("psutil.virtual_memory", return_value=Memory())
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
    )
    report = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD", hostname="", ip=""
    )
    report.scan_id = 1
    report.errors = ""

    await report.report()

    assert api_request_mock.call_args.kwargs["state"] == state
