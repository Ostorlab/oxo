"""Risk message asset for injecting risk reports onto the message bus."""

import dataclasses
from typing import Optional, Dict, Any

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.report.risk")
class Risk(asset.Asset):
    """Risk report to be injected onto the message bus."""

    description: str
    rating: str
    domain_name: Optional[Dict[str, Any]] = None
    ipv4: Optional[Dict[str, Any]] = None
    ipv6: Optional[Dict[str, Any]] = None
    link: Optional[Dict[str, Any]] = None
    android_store: Optional[Dict[str, Any]] = None
    ios_store: Optional[Dict[str, Any]] = None
    file: Optional[Dict[str, Any]] = None
    android_aab: Optional[Dict[str, Any]] = None
    android_apk: Optional[Dict[str, Any]] = None
    ios_ipa: Optional[Dict[str, Any]] = None
    api_schema: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:
        return f"Risk({self.rating}: {self.description})"
