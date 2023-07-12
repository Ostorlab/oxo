"""Reporter daemon logic that report scanner state periodically."""
import psutil
import dataclasses
import time

from ostorlab.apis.runners import public_runner
from ostorlab.apis import add_scanner_state

CAPTURE_INTERVAL = 300


@dataclasses.dataclass
class State:
    """Current scanner state."""

    scanner_id: int
    scan_id: int
    cpu_load: float
    memory_load: float
    total_cpu: int
    total_memory: int
    hostname: str
    ip: str
    errors: str


class Reporter:
    """Reporter collects information about the current scanner."""

    def __init__(
        self, scanner_id: int, scan_id: int, hostname: str, ip: str, errors: str
    ):
        self._state = State(
            scanner_id=scanner_id,
            scan_id=scan_id,
            cpu_load=0,
            total_cpu=0,
            memory_load=0,
            total_memory=0,
            hostname=hostname,
            ip=ip,
            errors=errors,
        )

    async def _capture_state(self):
        """Capture current scanner state."""
        self._state.cpu = psutil.cpu_percent(interval=1, percpu=False)
        self._state.memory = psutil.virtual_memory().percent
        self._state.total_cpu = psutil.cpu_count()
        self._state.total_memory = psutil.virtual_memory().total

    async def _report_state(self):
        runner = public_runner.PublicAPIRunner()
        _ = runner.execute(
            add_scanner_state.AddScannerStateAPIRequest(state=self._state)
        )

    async def run(self):
        while True:
            await self._capture_state()
            await self._report_state()
            time.sleep(CAPTURE_INTERVAL)
