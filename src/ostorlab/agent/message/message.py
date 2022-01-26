"""Message module in charge of data serialization and deserialization based on the source or destination selector.

Message are automatically serialised based on the selector. The format follows these rules:

* Message are serialised using the protobuf format. Protobuf is used as it is a binary compact serialization format that
support bytes types with no intermediary (expansive) encoding.
* Message follow a hierarchy where the fields of a child selector must contain all the fields of the parent message. For
instance if message of selector /foo/bor has the definition:

{
color: str
size: int
}

The message with selector /foo/bar/baz must have the fields `color` and `size`, for instance:

{
color: str
size: int
weight: int
}

"""
import dataclasses
from typing import Any, Dict

from ostorlab.agent.message import proto_dict
from ostorlab.agent.message import serializer


@dataclasses.dataclass
class Message:
    """Message data class used for both incoming and outgoing messages."""
    selector: str
    data: Dict[str, Any]
    raw: bytes

    @classmethod
    def from_data(cls, selector: str, data: Dict[str, Any]) -> 'Message':
        """Generate a message from a structured data and destination selector.

        This a convenience method to avoid directly handling protobuf messages and the not so friendly protobuf API.

        Args:
            selector: Target selector used to define the message format.
            data: Message data to be serialized to raw format.

        Returns:
            Message with both raw and data definitions.
        """
        raw = serializer.serialize(selector, data).SerializeToString()
        return cls(data=data, selector=selector, raw=raw)

    @classmethod
    def from_raw(cls, selector: str, raw: bytes) -> 'Message':
        """Generate a message from a raw data and source selector.

        This a convenience method to avoid directly handling protobuf messages and the not so friendly protobuf API.

        Args:
            selector: Source selector used to define the message format.
            raw: Message raw data to be deserialized to pythonic data structure.

        Returns:
            Message with both raw and data definitions.
        """
        proto_message = serializer.deserialize(selector, raw)
        data = proto_dict.protobuf_to_dict(proto_message, use_enum_labels=True)
        return cls(data=data, selector=selector, raw=raw)
