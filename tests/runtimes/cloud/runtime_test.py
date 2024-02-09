"""Unittest for cloud runtime."""
import io
import json
from typing import Dict, List, Optional, Union

from ostorlab.apis import request
from ostorlab.runtimes import definitions
from ostorlab.apis.runners import authenticated_runner
from ostorlab.runtimes.cloud import runtime as cloud_runtime


class MockCreateAgentGroupAPIRequest(request.APIRequest):
    """Persist agent group API request."""

    def __init__(
        self,
        name: Optional[str],
        description: str,
        agents: List[Dict[str, Union[str, List]]],
    ) -> None:
        """Initializer"""
        self._name = name
        self._description = description
        self._agents = agents

    @property
    def query(self) -> Optional[str]:
        """Sets the query of the API request.

        Returns:
            The query to create the agent group.
        """
        return """
            mutation PublishAgentGroup($agentGroup: AgentGroupCreateInputType!){
                publishAgentGroup(agentGroup: $agentGroup) {
                    agentGroup{
                        id
                    }
                }
            }
        """

    @property
    def data(self) -> Optional[Dict]:
        """Sets the body of the API request.

        Returns:
            The body of the create agent group request.
        """
        return {"query": self.query, "variables": {}}


def testRuntimeScanStop_whenScanIdIsValid_RemovesScanService(
    mocker, httpx_mock, data_list_agent, data_create_agent_group, data_create_asset
):
    """Unittest for the scan stop method when there are local scans available.
    Gets the docker services and checks for those with ostorlab.universe
    as one of the labels to find the service with the given scan id.
    Removes the scan service matching the provided id.
    """
    valid_yaml = """
        kind: "AgentGroup"
        description: "AgentGroup1 Should be here"
        image: "some/path/to/the/image"
        agents:
          - key: "agent/ostorlab/BigFuzzer"
            args:
              - name: "color"
                type: "string"
                value: "red"
              - name: "id"
                type: "number"
                value: 100
              - name: "is_hidden"
                type: "boolean"
                value: True
              - name: "urls"
                type: "array"
                value:
                    - "url1"
                    - "url2"
    """
    valid_yaml_def = io.StringIO(valid_yaml)

    httpx_mock.add_response(
        method="POST",
        url=authenticated_runner.AUTHENTICATED_GRAPHQL_ENDPOINT,
        json=data_list_agent
    )
    httpx_mock.add_response(
        method="POST",
        url=authenticated_runner.AUTHENTICATED_GRAPHQL_ENDPOINT,
        json=data_create_agent_group,
    )
    httpx_mock.add_response(
        method="POST",
        url=authenticated_runner.AUTHENTICATED_GRAPHQL_ENDPOINT,
        json=data_create_asset,
    )

    agent_group = definitions.AgentGroupDefinition.from_yaml(valid_yaml_def)
    mock_agent_group = mocker.patch(
        "ostorlab.apis.agent_group.CreateAgentGroupAPIRequest",
        side_effect=MockCreateAgentGroupAPIRequest,
    )

    cloud_runtime.CloudRuntime().scan(
        title="Cloud scan", agent_group_definition=agent_group, assets=[]
    )

    history = httpx_mock.get_requests()
    assert len(history) == 4
    assert mock_agent_group.call_args[0][2][0]["args"][0]["value"] == b"red"
    assert mock_agent_group.call_args[0][2][0]["args"][1]["value"] == b"100"
    assert mock_agent_group.call_args[0][2][0]["args"][2]["value"] == b"true"
    assert (
        mock_agent_group.call_args[0][2][0]["args"][3]["value"] == b'["url1", "url2"]'
    )
