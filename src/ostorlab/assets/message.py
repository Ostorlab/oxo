"""Generic message asset for injecting arbitrary protobuf messages onto the message bus."""

import dataclasses

from ostorlab.assets import asset


@dataclasses.dataclass
class Message(asset.Asset):
    """Generic message to be injected onto the message bus.

    Unlike other assets, the selector is dynamic and proto bytes are pre-computed.
    """

    selector: str
    proto_bytes: bytes

    def to_proto(self) -> bytes:
        return self.proto_bytes

    def __str__(self) -> str:
        return f"Message(selector={self.selector})"
