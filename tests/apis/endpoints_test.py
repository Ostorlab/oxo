"""Tests for the reporting engine endpoints derivation."""

import pytest

from ostorlab.apis.runners import endpoints


@pytest.mark.parametrize(
    "reporting_engine_url",
    ["https://re.example.com/apis/graphql", "https://re.example.com/apis/graphql/"],
)
def testPublicGraphqlEndpoint_whenReportingUrlProvided_returnsSiblingEndpoint(
    reporting_engine_url: str,
) -> None:
    """The public endpoint replaces the last path segment of the reporting endpoint."""
    assert (
        endpoints.public_graphql_endpoint(reporting_engine_url)
        == "https://re.example.com/apis/public_graphql"
    )


def testTokenEndpoint_whenReportingUrlProvided_returnsSiblingEndpoint() -> None:
    """The token endpoint replaces the last path segment of the reporting endpoint."""
    assert (
        endpoints.token_endpoint("http://localhost:8000/apis/graphql")
        == "http://localhost:8000/apis/token/"
    )


def testSiblingEndpoints_whenReportingUrlIsNone_returnNone() -> None:
    """Without a reporting endpoint, the runners keep their default endpoints."""
    assert endpoints.public_graphql_endpoint(None) is None
    assert endpoints.token_endpoint(None) is None


@pytest.mark.parametrize(
    "url",
    [
        "https://re.example.com/apis/graphql",
        "http://localhost:8000/apis/graphql",
        "http://127.0.0.1:8000/apis/graphql",
        "http://[::1]:8000/apis/graphql",
    ],
)
def testIsTransportSafe_whenHttpsOrLoopbackHttp_returnsTrue(url: str) -> None:
    """Credentials sent over https or to a loopback host are not exposed on the network."""
    assert endpoints.is_transport_safe(url) is True


@pytest.mark.parametrize(
    "url",
    [
        "http://re.example.com/apis/graphql",
        "http://10.0.0.5:8000/apis/graphql",
        "http://localhost.example.com/apis/graphql",
    ],
)
def testIsTransportSafe_whenHttpToRemoteHost_returnsFalse(url: str) -> None:
    """Plain http to any host other than loopback would send the credentials in cleartext."""
    assert endpoints.is_transport_safe(url) is False
