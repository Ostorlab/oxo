"""Unittest for scan list api."""
import json
from ostorlab.apis import scan_list


def testScanListAPIRequest_always_returnsData() -> None:
    scans_list_api = scan_list.ScansListAPIRequest(page=1, elements=10)

    expected_query = """
         query Scans($page: Int, $numberElements: Int) {
            scans(page: $page, numberElements: $numberElements) {
                pageInfo {
                    hasNext
                    hasPrevious
                    count
                    numPages
                }
                scans {
                    assetType
                    riskRating
                    version
                    packageName
                    id
                    progress
                    createdTime
                    scanProfile
                }
            }
         }
        """
    assert scans_list_api.query == expected_query

    expected_data = {
        "query": expected_query,
        "variables": json.dumps({"page": 1, "numberElements": 10}),
    }
    assert scans_list_api.data == expected_data
