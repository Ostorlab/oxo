"""Ios testflight target asset"""

import dataclasses

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.asset.store.ios_testflight")
class IOSTestflight(asset.Asset):
    """iOS testflight target asset."""

    def __init__(self, application_url: str):
        self.application_url = application_url

    def __str__(self) -> str:
        return f"iOS Testflight ({self.application_url})"

    @property
    def proto_field(self) -> str:
        return "ios_testflight"
