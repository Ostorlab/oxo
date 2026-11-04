"""Derives the API sibling endpoints from a configured GraphQL endpoint."""

import ipaddress
from urllib import parse


def _sibling_endpoint(api_url: str | None, path: str) -> str | None:
    if api_url is None:
        return None
    return parse.urljoin(api_url.rstrip("/"), path)


def public_graphql_endpoint(api_url: str | None) -> str | None:
    """Public GraphQL endpoint served next to the Ostorlab API GraphQL endpoint.

    Args:
        api_url: The Ostorlab API GraphQL endpoint, None for the default one.

    Returns:
        The public GraphQL endpoint, None to keep the default one.
    """
    return _sibling_endpoint(api_url, "public_graphql")


def token_endpoint(api_url: str | None) -> str | None:
    """Token endpoint served next to the Ostorlab API GraphQL endpoint.

    Args:
        api_url: The Ostorlab API GraphQL endpoint, None for the default one.

    Returns:
        The token endpoint, None to keep the default one.
    """
    return _sibling_endpoint(api_url, "token/")


def is_transport_safe(url: str) -> bool:
    """Whether the credentials the runners send to the URL are protected in transit.

    https always is. Plain http is accepted only for a loopback host, whose traffic never
    leaves the machine.

    Args:
        url: An API or scanner endpoint.

    Returns:
        True for https, or http to localhost, 127.0.0.0/8 or ::1.
    """
    parsed_url = parse.urlparse(url)
    if parsed_url.scheme == "https":
        return True
    if parsed_url.scheme != "http" or parsed_url.hostname is None:
        return False
    if parsed_url.hostname == "localhost":
        return True
    try:
        return ipaddress.ip_address(parsed_url.hostname).is_loopback
    except ValueError:
        return False
