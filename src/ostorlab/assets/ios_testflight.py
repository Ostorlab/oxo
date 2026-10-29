"""Ios testflight target asset"""

import dataclasses

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.asset.store.ios_testflight")
class IOSTestflight(asset.Asset):
    """iOS testflight target asset."""

    application_url: str | None = None
    app_name: str | None = None

    def __str__(self) -> str:
        if self.application_url is not None:
            return f"iOS Testflight ({self.application_url})"
        return f"iOS Testflight ({self.app_name})"

    @property
    def proto_field(self) -> str:
        return "ios_testflight"
