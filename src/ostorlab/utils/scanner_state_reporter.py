"""Reporter logic to read the scanner state periodically and send it to the backend."""
import psutil
import time

from ostorlab.apis.runners import authenticated_runner
from ostorlab.apis import add_scanner_state
from ostorlab.utils import defintions


class ScannerStateReporter:
    """Reporter collects information about the current scanner."""

    def __init__(
        self,
        scanner_id: int,
        scan_id: int | None,
        hostname: str,
        ip: str,
        errors: str | None,
    ):
        self._scanner_id = scanner_id
        self._scan_id = scan_id
        self._hostname = hostname
        self._ip = ip
        self._errors = errors

    def _capture_state(self) -> defintions.ScannerState:
        """Capture current scanner state."""
        state = defintions.ScannerState(
            scanner_id=self._scanner_id,
            scan_id=self._scan_id,
            cpu_load=psutil.cpu_percent(interval=1, percpu=False),
            total_cpu=psutil.cpu_count(),
            memory_load=psutil.virtual_memory().percent,
            total_memory=psutil.virtual_memory().total >> 30,  # total memory in GB
            hostname=self._hostname,
            ip=self._ip,
            errors=self._errors,
        )
        return state

    def _report_state(self, state: defintions.ScannerState) -> None:
        runner = authenticated_runner.AuthenticatedAPIRunner()
        _ = runner.execute(add_scanner_state.AddScannerStateAPIRequest(state=state))

    async def report(self) -> None:
        """Capture the current state of the scanner and persist it."""
        state = self._capture_state()
        self._report_state(state)
