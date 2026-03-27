"""Risk message asset for injecting risk reports onto the message bus."""

import dataclasses
from typing import Any, Optional

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.report.risk")
class Risk(asset.Asset):
    """Risk report to be injected onto the message bus."""

    description: str
    rating: str
    domain_name: Optional[dict[str, Any]] = None
    ipv4: Optional[dict[str, Any]] = None
    ipv6: Optional[dict[str, Any]] = None
    link: Optional[dict[str, Any]] = None
    android_store: Optional[dict[str, Any]] = None
    ios_store: Optional[dict[str, Any]] = None
    file: Optional[dict[str, Any]] = None
    android_aab: Optional[dict[str, Any]] = None
    android_apk: Optional[dict[str, Any]] = None
    ios_ipa: Optional[dict[str, Any]] = None
    api_schema: Optional[dict[str, Any]] = None

    @property
    def proto_field(self) -> str:
        return "risk"

    def __str__(self) -> str:
        return f"Risk({self.rating}: {self.description})"
