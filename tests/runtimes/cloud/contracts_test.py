"""Successful cloud operations and capability refusals retain their contracts."""

import pytest
from pytest_httpx import HTTPXMock

from ostorlab import configuration_manager
from ostorlab.assets import ipv4
from ostorlab.runtimes import definitions
from ostorlab.runtimes.cloud import runtime as cloud_runtime


def testCloudScan_whenRequestsSucceed_returnsNone(httpx_mock: HTTPXMock) -> None:
    """Cloud scan success does not acquire a local scan return value."""
    httpx_mock.add_response(
        json={"data": {"publishAgentGroup": {"agentGroup": {"id": "1"}}}}
    )
    httpx_mock.add_response(json={"data": {"createAsset": {"asset": {"id": "2"}}}})
    httpx_mock.add_response(json={"data": {"createAgentScan": {"scan": {"id": "3"}}}})

    assert (
        cloud_runtime.CloudRuntime().scan(
            "test",
            definitions.AgentGroupDefinition(agents=[]),
            [ipv4.IPv4(host="8.8.8.8", mask="32")],
        )
        is None
    )


def testCloudStop_whenRequestSucceeds_returnsNone(httpx_mock: HTTPXMock) -> None:
    """Cloud stop success retains its legacy None return contract."""
    httpx_mock.add_response(json={"data": {"stopScan": {"scan": {"id": "123"}}}})

    assert cloud_runtime.CloudRuntime().stop(123) is None


@pytest.mark.parametrize("authenticated", [False, True])
def testCloudCanRun_whenUnauthenticatedOrAgentUnsupported_returnsFalse(
    authenticated: bool,
    httpx_mock: HTTPXMock,
) -> None:
    """Capability checks intentionally refuse missing credentials or agents."""
    configuration_manager.ConfigurationManager().api_key = (
        "test" if authenticated else None
    )
    if authenticated:
        httpx_mock.add_response(json={"errors": [{"message": "Agent does not exist"}]})

    assert (
        cloud_runtime.CloudRuntime().can_run(
            definitions.AgentGroupDefinition(
                agents=[definitions.AgentSettings(key="agent/ostorlab/missing")]
            )
        )
        is False
    )
