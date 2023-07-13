"""Testing module for the scanner state reporter class."""

import pytest
import pytest_mock

from ostorlab.utils import scanner_state_reporter
from ostorlab.utils.defintions import ScannerState


class Memory:
    percent: float = 10
    total: int = 100


@pytest.mark.asyncio
async def testReportMethod_whenCalled_updateValuesCorrectly(mocker: pytest_mock.MockerFixture) -> None:
    """Test the report method to insure that the values filled from the private capture_state method are correct."""
    mocker.patch(
        "ostorlab.apis.runners.authenticated_runner.AuthenticatedAPIRunner.execute"
    )
    mocker.patch("psutil.cpu_percent", return_value=10)
    mocker.patch("psutil.cpu_count", return_value=10)
    mocker.patch("psutil.virtual_memory", return_value=Memory())
    mock = mocker.patch("ostorlab.apis.add_scanner_state.AddScannerStateAPIRequest")
    state = ScannerState(
        scanner_id=1,
        scan_id=1,
        cpu_load=10,
        total_cpu=10,
        memory_load=10,
        total_memory=100,
        hostname="",
        ip="",
        errors="",
    )

    report = scanner_state_reporter.ScannerStateReporter(
        scanner_id=1, scan_id=1, hostname="", ip="", errors=""
    )
    await report.report()

    assert mock.call_args.kwargs["state"] == state
