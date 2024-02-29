"""Utils to handle IP operations."""

from typing import Optional
import socket


def get_ip() -> Optional[str]:
    """Returns the machine IP address."""
    return socket.gethostbyname(socket.gethostname())
