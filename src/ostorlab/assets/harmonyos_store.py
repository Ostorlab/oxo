"""HarmonyOS store asset representation."""

import dataclasses
from typing import Optional

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.asset.store.harmonyos_store")
class HarmonyOSStore(asset.Asset):
    """Represents a HarmonyOS store reference (bundle name)."""

    bundle_name: Optional[str] = None

    def __str__(self) -> str:
        return f"Harmonyos Store: ({self.bundle_name})"

    @property
    def proto_field(self) -> str:
        return "harmonyos_store"
