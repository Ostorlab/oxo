"""Definition of the emitting protocol exposing the emit method."""

from typing import Any, Dict, Protocol, Optional


class EmitProtocol(Protocol):
    """Protocol exposing the emit method."""

    def emit(
        self, selector: str, data: Dict[str, Any], message_id: Optional[str] = None
    ) -> None:
        """Sends a message to all listening agents on the specified selector.

        Args:
            selector: target selector.
            data: message data to be serialized.
            message_id: An id that will be added to the tail of the message.
        Raises:
            NonListedMessageSelectorError: when selector is not part of listed out selectors.

        Returns:
            None
        """
        pass
