"""Agent release channels: the prerelease stream a scan resolves agent versions from.

A scan without a channel, `None`, resolves stable versions.
"""

import re

CHANNEL_PATTERN = re.compile(r"^[a-z][a-z0-9-]{0,31}$")


def is_valid(channel: str) -> bool:
    """Check whether a release channel name is valid.

    Args:
        channel: The release channel name.

    Returns:
        True when the name matches the release channel pattern.
    """
    return CHANNEL_PATTERN.fullmatch(channel) is not None
