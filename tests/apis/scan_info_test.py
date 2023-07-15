"""Unittest for scan info api"""
import json
from ostorlab.apis import scan_info


def testScanInfoAPIRequest_always_returnsData() -> None:
    scan_info_api = scan_info.ScanInfoAPIRequest(scan_id=12345)

    assert scan_info_api._scan_id == 12345

    expected_query = """
         query scan($scanId: Int) {
            scan(scanId: $scanId) {
                progress
                riskRating
            }
         }
        """
    assert scan_info_api.query == expected_query

    expected_data = {
        "query": expected_query,
        "variables": json.dumps({"scanId": 12345}),
    }
    assert scan_info_api.data == expected_data
