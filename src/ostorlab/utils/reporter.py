"""Reporter daemon logic that report scanner state periodically."""
import psutil
import time

from ostorlab.apis.runners import authenticated_runner
from ostorlab.apis import add_scanner_state
from ostorlab.utils import defintions


class Reporter:
    """Reporter collects information about the current scanner."""

    def __init__(
        self,
        scanner_id: int,
        scan_id: int,
        hostname: str,
        ip: str,
        errors: str,
        capture_interval: int = 300,
    ):
        self.capture_interval = capture_interval
        self.state = defintions.State(
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

    async def capture_state(self) -> None:
        """Capture current scanner state."""

        self.state.cpu_load = psutil.cpu_percent(interval=1, percpu=False)
        self.state.memory_load = psutil.virtual_memory().percent
        self.state.total_cpu = psutil.cpu_count()
        self.state.total_memory = psutil.virtual_memory().total

    async def _report_state(self) -> None:
        runner = authenticated_runner.AuthenticatedAPIRunner()
        _ = runner.execute(
            add_scanner_state.AddScannerStateAPIRequest(state=self.state)
        )

    async def run(self) -> None:
        while True:
            await self.capture_state()
            await self._report_state()
            time.sleep(self.capture_interval)
