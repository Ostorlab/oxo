"""Derives the reporting engine sibling endpoints from a configured GraphQL endpoint."""

from urllib import parse


def _sibling_endpoint(reporting_engine_url: str | None, path: str) -> str | None:
    if reporting_engine_url is None:
        return None
    return parse.urljoin(reporting_engine_url.rstrip("/"), path)


def public_graphql_endpoint(reporting_engine_url: str | None) -> str | None:
    """Public GraphQL endpoint served next to the reporting engine GraphQL endpoint.

    Args:
        reporting_engine_url: The reporting engine GraphQL endpoint, None for the default one.

    Returns:
        The public GraphQL endpoint, None to keep the default one.
    """
    return _sibling_endpoint(reporting_engine_url, "public_graphql")


def token_endpoint(reporting_engine_url: str | None) -> str | None:
    """Token endpoint served next to the reporting engine GraphQL endpoint.

    Args:
        reporting_engine_url: The reporting engine GraphQL endpoint, None for the default one.

    Returns:
        The token endpoint, None to keep the default one.
    """
    return _sibling_endpoint(reporting_engine_url, "token/")
