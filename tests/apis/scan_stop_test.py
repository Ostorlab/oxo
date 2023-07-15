"""Unittest for scan stop api."""
import json
from ostorlab.apis import scan_stop


def testScanStopAPIRequest_always_returnData() -> None:
    scan_stop_api = scan_stop.ScanStopAPIRequest(scan_id=12345)

    assert scan_stop_api._scan_id == 12345

    expected_query = """
         mutation StopScanMutation($scanId: Int!) {
            stopScan(scanId: $scanId) {
                scan {
                    id
                }
            }
         }
        """
    assert scan_stop_api.query == expected_query

    expected_data = {
        "query": expected_query,
        "variables": json.dumps({"scanId": 12345}),
    }
    assert scan_stop_api.data == expected_data
