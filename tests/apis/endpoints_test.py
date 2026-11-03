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
