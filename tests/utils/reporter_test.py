"""Testing module for the scanner state reporter class."""

import pytest

from ostorlab.utils import reporter


@pytest.mark.asyncio
async def testCaptureState_whenCalled_updateValues() -> None:
    report = reporter.Reporter(scanner_id=1, scan_id=1, hostname="", ip="", errors="")
    await report.capture_state()

    assert report.state.cpu_load != 0
    assert report.state.total_cpu != 0
    assert report.state.memory_load != 0
    assert report.state.total_memory != 0
