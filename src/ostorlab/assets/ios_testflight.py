"""Ios testflight target asset"""

import dataclasses
from typing import Union, cast

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.asset.store.ios_testflight")
class IOSTestflight(asset.Asset):
    """iOS testflight target asset."""

    application_url: str

    def __str__(self) -> str:
        return f"iOS Testflight ({self.application_url})"

    @classmethod
    def from_dict(cls, data: dict[str, Union[str, bytes]]) -> "IOSTestflight":
        """Constructs an IOSTestflight asset from a dictionary."""

        application_url = data.get("application_url", "")
        if application_url == "":
            raise ValueError("application_url is missing.")
        return cls(
            application_url=cast(
                str,
                application_url.decode()
                if type(application_url) is bytes
                else application_url,
            )
        )

    @property
    def proto_field(self) -> str:
        return "ios_testflight"
