"""Ios testflight target asset"""

import dataclasses

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.asset.store.ios_testflight")
class IOSTestflight(asset.Asset):
    """iOS testflight target asset."""

    application_url: str

    def __str__(self) -> str:
        return f"iOS Testflight ({self.application_url})"

    @property
    def proto_field(self) -> str:
        return "ios_testflight"
