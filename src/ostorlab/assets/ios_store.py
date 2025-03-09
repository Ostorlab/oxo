"""Ios bundle_id target asset"""

import dataclasses

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.asset.store.ios_store")
class IOSStore(asset.Asset):
    """Ios bundle target asset."""

    bundle_id: str

    def __str__(self) -> str:
        return f"iOS Store ({self.bundle_id})"

    @classmethod
    def from_dict(cls, data: dict[str, str | bytes]) -> "IOSStore":
        """Constructs an IOSStore asset from a dictionary."""
        bundle_id = data.get("bundle_id", "")
        if type(bundle_id) is bytes:
            bundle_id = bundle_id.decode()
        if bundle_id == "":
            raise ValueError("bundle_id is missing.")
        return IOSStore(bundle_id)  # type: ignore

    @property
    def proto_field(self) -> str:
        return "ios_store"
