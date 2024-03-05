"""Reporter logic to read the scanner state periodically and send it to the backend."""

from ostorlab.apis.runners import authenticated_runner
from ostorlab.apis import add_scanner_state
from ostorlab.utils import defintions


class ScannerStateReporter:
    """Reporter collects information about the current scanner."""

    def __init__(
        self,
        scanner_id: str,
        hostname: str,
        ip: str,
    ):
        self._scanner_id = scanner_id
        self.scan_id = None
        self._hostname = hostname
        self._ip = ip

    def _capture_state(self) -> defintions.ScannerState:
        """Capture current scanner state."""
        try:
            import psutil

            state = defintions.ScannerState(
                scanner_id=self._scanner_id,
                scan_id=self.scan_id,
                cpu_load=psutil.cpu_percent(interval=1, percpu=False),
                total_cpu=psutil.cpu_count(),
                memory_load=psutil.virtual_memory().percent,
                total_memory=psutil.virtual_memory().total >> 30,  # total memory in GB
                hostname=self._hostname,
                ip=self._ip,
            )
        except ImportError:
            state = defintions.ScannerState(
                scanner_id=self._scanner_id,
                scan_id=self.scan_id,
                cpu_load=0,
                total_cpu=0,
                memory_load=0,
                total_memory=0,  # total memory in GB
                hostname=self._hostname,
                ip=self._ip,
            )

        return state

    def _report_state(self, state: defintions.ScannerState) -> None:
        runner = authenticated_runner.AuthenticatedAPIRunner()
        _ = runner.execute(add_scanner_state.AddScannerStateAPIRequest(state=state))

    async def report(self) -> None:
        """Capture the current state of the scanner and persist it."""
        state = self._capture_state()
        self._report_state(state)
