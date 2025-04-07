"""Unittest for cloud runtime."""

import io
from typing import Dict, List, Optional, Union
from unittest import mock

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
        json=data_list_agent,
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


def testCloudDescribeVuln_whenVulnHasExploitationAndPostExploitationDetails_printsExploitationAndPostExploitationDetails(
    mocker: mock.MagicMock, httpx_mock: mock.MagicMock
):
    """Tests describe_vuln method with vulnerability containing exploitation_detail and post_exploitation_detail.
    Should print these details to console.
    """
    mock_console = mock.MagicMock()
    mock_table = mock.MagicMock()
    mock_print = mock.MagicMock()
    mock_success = mock.MagicMock()
    mock_console.table = mock_table
    mock_console.print = mock_print
    mock_console.success = mock_success
    mocker.patch(
        "ostorlab.runtimes.cloud.runtime.cli_console.Console", return_value=mock_console
    )
    mocker.patch("ostorlab.runtimes.cloud.runtime.console", mock_console)
    mock_rich_print = mocker.patch("ostorlab.runtimes.cloud.runtime.rich.print")
    vulnerability_with_exploitation_details = {
        "data": {
            "scan": {
                "vulnerabilities": {
                    "vulnerabilities": [
                        {
                            "id": "123",
                            "customRiskRating": "HIGH",
                            "detail": {
                                "cvssV3Vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                                "title": "Test Vulnerability",
                                "shortDescription": "This is a test vulnerability",
                                "description": "Detailed description of the vulnerability",
                                "recommendation": "How to fix the vulnerability",
                                "references": [
                                    {"title": "Reference", "url": "https://example.com"}
                                ],
                            },
                            "technicalDetail": "Technical details about the vulnerability",
                            "technicalDetailFormat": "MARKDOWN",
                            "vulnerabilityLocation": {"asset": {"name": "example.com"}},
                            "exploitation_detail": "How to exploit this vulnerability",
                            "post_exploitation_detail": "What to do after exploitation",
                        }
                    ],
                    "pageInfo": {"hasNext": False, "numPages": 1},
                }
            }
        }
    }
    httpx_mock.add_response(
        method="POST",
        url=authenticated_runner.AUTHENTICATED_GRAPHQL_ENDPOINT,
        json=vulnerability_with_exploitation_details,
    )
    mocker.patch("ostorlab.runtimes.cloud.runtime.click.confirm", return_value=False)
    runtime = cloud_runtime.CloudRuntime()

    runtime.describe_vuln(scan_id=1, vuln_id=None)

    assert mock_table.call_count == 1
    assert (
        mock_rich_print.call_count >= 6
    )  # At least 6 panels (4 standard + 2 for exploitation details)
    exploitation_panel_calls = [
        call
        for call in mock_rich_print.call_args_list
        if "Exploitation details" in call[0][0].title
        or "Post Exploitation details" in call[0][0].title
    ]
    assert len(exploitation_panel_calls) == 2
    assert mock_success.call_count == 1
