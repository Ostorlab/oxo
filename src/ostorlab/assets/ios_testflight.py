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

    @classmethod
    def from_dict(cls, data: dict[str, str | bytes]) -> "IOSTestflight":
        """Constructs an IOSTestflight asset from a dictionary."""
        application_url = data.get("application_url", "")
        if type(application_url) is bytes:
            application_url = application_url.decode()
        if application_url == "":
            raise ValueError("package_name is missing.")
        return IOSTestflight(application_url)  # type: ignore

    @property
    def proto_field(self) -> str:
        return "ios_testflight"
