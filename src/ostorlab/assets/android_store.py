"""Android store package target asset."""

import dataclasses

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.asset.store.android_store")
class AndroidStore(asset.Asset):
    """Android store package target asset."""

    package_name: str

    def __str__(self) -> str:
        return f"Android Store: ({self.package_name})"

    @property
    def proto_field(self) -> str:
        return "android_store"
