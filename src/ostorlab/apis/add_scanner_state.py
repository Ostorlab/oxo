"""Add scanner state via an API Request."""

from typing import Dict, Optional
import json

from ostorlab.apis import request
from ostorlab.utils import defintions


class AddScannerStateAPIRequest(request.APIRequest):
    """Report the scanner state."""

    def __init__(self, state: defintions.ScannerState):
        """Sets the state values.

        Args:
           state: A dataclass instance holding state info of a runner.
        """
        self._state = state

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
            "query": self.query,
            "variables": json.dumps(
                {
                    "scannerState": {
                        "scannerUuid": self._state.scanner_id,
                        "scanId": self._state.scan_id,
                        "hostname": self._state.hostname,
                        "ipAddress": self._state.ip,
                        "memoryLoad": self._state.memory_load,
                        "totalMemory": self._state.total_memory,
                        "cpuLoad": self._state.cpu_load,
                        "totalCpu": self._state.total_cpu,
                    }
                }
            ),
        }
        return data
