"""Add scanner state via an API Request."""
from typing import Dict, Optional

from ostorlab.apis import request
from ostorlab.runtimes import reporter as rep


class AddScannerStateAPIRequest(request.APIRequest):
    """Report the scanner state."""

    def __init__(self, state: rep.State):
        """Sets the state values.

        Args:
           state: A dataclass instance holding state info of a runner.
        """
        self.state = state

    @property
    def query(self) -> Optional[str]:
        """Defines the query to report the scanner state.

        Returns:
            The query to report the scanner state
        """
        return """
        mutation AddScannerState($scannerState: ScannerStateInputType!) {
          addScannerState(scannerState: $scannerState) {
            scannerState {
              scanId
              scanner {
                id
              }
            }
          }
        }
    """

    @property
    def data(self) -> Optional[Dict]:
        """Sets the variables to add the scanner state.

        Returns:
              The variables dict to add the scanner state.
        """
        data = {
            "scannerState": {
                "scannerId": self.state.scanner_id,
                "scanId": self.state.scan_id,
                "hostname": self.state.hostname,
                "ipAddress": self.state.ip,
                "memoryLoad": self.state.memory_load,
                "totalMemory": self.state.total_memory,
                "cpuLoad": self.state.cpu_load,
                "totalCpu": self.state.total_cpu,
                "errors": self.state.errors,
            }
        }
        return data
