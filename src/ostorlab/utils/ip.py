"""Utils to handle IP operations."""

import socket


def get_ip() -> str | None:
    """Returns the machine IP address."""
    return socket.gethostbyname(socket.gethostname())
