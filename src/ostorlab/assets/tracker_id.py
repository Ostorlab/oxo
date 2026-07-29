"""Tracker id asset definition."""

import dataclasses

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.asset.tracker_id")
class TrackerId(asset.Asset):
    """Tracking identifier asset.

    A tracking identifier (for example an advertising identifier or an analytics
    SDK identifier) discovered by an agent and correlated across assets.
    """

    id: str
    source: str

    def __str__(self) -> str:
        return f"Tracker id {self.id} from {self.source}"

    @property
    def proto_field(self) -> str:
        return "tracker_id"
