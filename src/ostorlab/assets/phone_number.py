"""Phone number asset definition."""

import dataclasses

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.asset.phone_number")
class PhoneNumber(asset.Asset):
    """Phone Number target asset."""

    number: str

    def __str__(self) -> str:
        return self.number

    @property
    def proto_field(self) -> str:
        return "phone_number"
