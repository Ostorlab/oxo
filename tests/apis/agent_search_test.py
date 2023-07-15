"""Unittests for testing the agent search"""
from ostorlab.apis import agent_search


def testAgentSearch_always_returnData():
    agent_search_api = agent_search.AgentSearchAPIRequest(search="agent")

    assert agent_search_api.data["variables"] == '{"search": "agent"}'

    assert (
        agent_search_api.data["query"]
        == """
            query Agents($search: String!){
                agents(search: $search) {
                    agents {
                        key
                        versions (orderBy:Version, sort:Desc, numberElements:1, page:1) {
                            versions {
                                key
                                version
                                description
                                inSelectors
                                outSelectors
                              }
              
                        }
                    }
                }
            }
        """
    )
