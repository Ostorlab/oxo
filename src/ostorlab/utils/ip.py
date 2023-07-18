"""Utils to handle IP operations."""
from typing import Optional

import requests


def get_public_ip() -> Optional[str]:
    """Returns the machine public IP address."""
    try:
        # Make a request to the ipify API
        response = requests.get("https://api.ipify.org?format=json", timeout=30)
        if response.status_code == 200:
            ip_address = str(response.json()["ip"])
            return ip_address
        else:
            return None
    except requests.RequestException:
        return None
