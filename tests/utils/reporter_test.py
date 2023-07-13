"""Testing module for the scanner state reporter class."""

import pytest

from ostorlab.utils import reporter
import mock


class Memory:
    percent: float = 10
    total: int = 100


@pytest.mark.asyncio
async def testReport_whenCalled_updateValues(mocker) -> None:

    mocker.patch(
        "ostorlab.apis.runners.authenticated_runner.AuthenticatedAPIRunner.execute",
        mock.Mock(return_value="dummy"),
    )
    mocker.patch("psutil.cpu_percent", mock.Mock(return_value=10))
    mocker.patch("psutil.cpu_count", mock.Mock(return_value=10))
    mocker.patch("psutil.virtual_memory", return_value=Memory())
    report = reporter.Reporter(scanner_id=1, scan_id=1, hostname="", ip="", errors="")
    await report.report()

    assert report.state.cpu_load == 10
    assert report.state.total_cpu == 10
    assert report.state.memory_load == 10
    assert report.state.total_memory == 100
