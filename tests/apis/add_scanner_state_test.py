"""Unittests for testing the scanner state"""
from ostorlab.apis import add_scanner_state


def testAddScannerState_always_returnData(scanner_state):
    scanner_state_api = add_scanner_state.AddScannerStateAPIRequest(scanner_state)

    assert scanner_state_api.data["scannerState"]["scannerId"] == 122
    assert scanner_state_api.data["scannerState"]["scanId"] == 1
    assert scanner_state_api.data["scannerState"]["cpuLoad"] == 50.9
    assert scanner_state_api.data["scannerState"]["memoryLoad"] == 40.2
    assert scanner_state_api.data["scannerState"]["totalCpu"] == 3
    assert scanner_state_api.data["scannerState"]["totalMemory"] == 100
    assert scanner_state_api.data["scannerState"]["hostname"] == "test"
    assert scanner_state_api.data["scannerState"]["ipAddress"] == "0.0.0.0"
    assert scanner_state_api.data["scannerState"]["errors"] == "error"

    assert (
        scanner_state_api.query
        == """\n        mutation AddScannerState($scannerState: ScannerStateInputType!) {
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
    )
