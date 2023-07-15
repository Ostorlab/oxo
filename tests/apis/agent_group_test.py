"""Unittests for testing the agent group"""
from ostorlab.apis import agent_group


def testAgentGroup_always_returnData(agent):
    agent_group_api = agent_group.CreateAgentGroupAPIRequest(
        name="AGG", description="Agent group", agents=[agent]
    )

    assert agent_group_api.data["variables"] == {
        "agentGroup": {
            "name": "AGG",
            "description": "Agent group",
            "access": "PRIVATE",
            "agents": [{"name": "test_agent"}],
        }
    }

    assert (
        agent_group_api.data["query"]
        == """
            mutation PublishAgentGroup($agentGroup: AgentGroupCreateInputType!){
                publishAgentGroup(agentGroup: $agentGroup) {
                    agentGroup{
                        id
                    }
                }
            }
        """
    )
