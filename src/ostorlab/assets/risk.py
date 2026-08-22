"""Risk asset."""

import dataclasses
from typing import Optional, Any

from ostorlab.assets import asset
from ostorlab.agent.message import serializer

PROTO_FIELD = "risk"
CLASS_NAME = "Risk"


@dataclasses.dataclass
@asset.selector("v3.asset.risk")
class Risk(asset.Asset):
    """Risk target asset."""

    rating: str
    description: str
    target: Optional[asset.Asset] = None
    domain_name: Optional[Any] = None
    ipv4: Optional[Any] = None
    ipv6: Optional[Any] = None
    link: Optional[Any] = None
    android_store: Optional[Any] = None
    ios_store: Optional[Any] = None
    file: Optional[Any] = None
    android_aab: Optional[Any] = None
    android_apk: Optional[Any] = None
    ios_ipa: Optional[Any] = None
    api_schema: Optional[Any] = None
    ios_testflight: Optional[Any] = None

    def __str__(self) -> str:
        if self.target is not None:
            return f"{CLASS_NAME} ({self.rating}): {self.description} -> {self.target}"
        return f"{CLASS_NAME} ({self.rating}): {self.description}"

    @property
    def proto_field(self) -> str:
        return PROTO_FIELD

    def to_proto(self) -> Any:
        if self.selector is None:
            raise asset.MissingTargetSelector()
        data: dict[str, Any] = {
            "rating": self.rating,
            "description": self.description,
        }
        if self.target is not None:
            if isinstance(self.target, asset.Asset):
                data[self.target.proto_field] = self.target.__dict__
            elif isinstance(self.target, dict):
                data.update(self.target)

        for field in (
            "domain_name",
            "ipv4",
            "ipv6",
            "link",
            "android_store",
            "ios_store",
            "file",
            "android_aab",
            "android_apk",
            "ios_ipa",
            "api_schema",
            "ios_testflight",
        ):
            val = getattr(self, field, None)
            if val is not None:
                if isinstance(val, asset.Asset):
                    data[val.proto_field] = val.__dict__
                else:
                    data[field] = val

        return serializer.serialize(self.selector, data).SerializeToString()
