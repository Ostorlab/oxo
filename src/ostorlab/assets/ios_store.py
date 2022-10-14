"""Ios bundle_id target asset"""
import dataclasses

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector('v3.asset.store.ios_store')
class IOSStore(asset.Asset):
    """Ios bundle target asset."""

    def __init__(self, bundle_id: str):
        self.bundle_id = bundle_id

    def __str__(self):
        return f'IOS store bundle_id ({self.path})'
