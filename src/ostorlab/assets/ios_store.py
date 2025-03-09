"""Ios bundle_id target asset"""

import dataclasses
from typing import Union

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.asset.store.ios_store")
class IOSStore(asset.Asset):
    """Ios bundle target asset."""

    bundle_id: str

    def __str__(self) -> str:
        return f"iOS Store ({self.bundle_id})"

    @classmethod
    def from_dict(cls, data: dict[str, Union[str, bytes]]) -> "IOSStore":
        """Constructs an IOSStore asset from a dictionary."""

        bundle_id = data.get("bundle_id", "")
        if bundle_id == "":
            raise ValueError("bundle_id is missing.")

        return cls(
            bundle_id=bundle_id.decode() if type(bundle_id) is bytes else bundle_id  # type: ignore
        )

    @property
    def proto_field(self) -> str:
        return "ios_store"
