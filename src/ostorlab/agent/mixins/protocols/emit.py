"""Definition of the emitting protocol exposing the emit method."""

from typing import Any, Protocol


class EmitProtocol(Protocol):
    """Protocol exposing the emit method."""

    def emit(
        self,
        selector: str,
        data: dict[str, Any],
        message_id: str | None = None,
        message_priority: int | None = None,
    ) -> None:
        """Sends a message to all listening agents on the specified selector.

        Args:
            selector: target selector.
            data: message data to be serialized.
            message_id: An id that will be added to the tail of the message.
            message_priority: Optional priority for the message, used by priority queues.
                Defaults to None.
        Raises:
            NonListedMessageSelectorError: when selector is not part of listed out selectors.

        Returns:
            None
        """
