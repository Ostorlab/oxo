"""Risk message asset for injecting risk reports onto the message bus."""

import dataclasses
from typing import Optional, Dict

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.report.risk")
class Risk(asset.Asset):
    """Risk report to be injected onto the message bus."""

    description: str
    rating: str
    domain_name: Optional[Dict] = None
    ipv4: Optional[Dict] = None
    ipv6: Optional[Dict] = None
    link: Optional[Dict] = None
    android_store: Optional[Dict] = None
    ios_store: Optional[Dict] = None
    file: Optional[Dict] = None
    android_aab: Optional[Dict] = None
    android_apk: Optional[Dict] = None
    ios_ipa: Optional[Dict] = None
    api_schema: Optional[Dict] = None

    def __str__(self) -> str:
        return f"Risk({self.rating}: {self.description})"
