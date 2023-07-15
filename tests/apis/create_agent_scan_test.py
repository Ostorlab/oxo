"""Unittests for testing the create agent scan api"""
from ostorlab.apis import create_agent_scan


def testCreateAgentScan_always_returnData():
    agent_create_scan_api = create_agent_scan.CreateAgentScanAPIRequest(
        title="AGS1", asset_id=1, agent_group_id=1
    )

    assert (
        agent_create_scan_api.data["variables"]
        == '{"scan": {"title": "AGS1", "assetId": 1, "agentGroupId": 1}}'
    )

    assert (
        agent_create_scan_api.data["query"]
        == """
            mutation StartAgentScan($scan: AgentScanInputType!){
                createAgentScan(scan: $scan) {
                    scan{
                        id
                    }
                }
            }
        """
    )
