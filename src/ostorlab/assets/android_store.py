"""Android .AAB asset."""
import dataclasses

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector('v3.asset.store.android_store')
class AndroidStore(asset.Asset):
    """Android store package target asset."""

    def __init__(self, package_name: str):
        self.package_name = package_name

    def __str__(self):
        return f'Android Store: {self.package_name}'