"""Unittests for testing the agent details"""
from ostorlab.apis import agent_details


def testAddScannerState_always_returnData():
    agent_detail_api = agent_details.AgentDetailsAPIRequest(agent_key="KEY_123")

    assert agent_detail_api.data["variables"] == '{"agentKey": "KEY_123"}'

    assert (
        agent_detail_api.data["query"]
        == """
            query Agent($agentKey: String!){
                agent(agentKey: $agentKey) {
                    name,
                    gitLocation,
                    yamlFileLocation,
                    dockerLocation,
                    access,
                    listable,
                    key
                    versions(orderBy: Version, sort: Desc, page: 1, numberElements: 1) {
                      versions {
                        version
                      }
                    }
                }
            }
        """
    )
