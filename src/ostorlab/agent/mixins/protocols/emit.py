"""Definition of the emitting protocol exposing the emit method."""
from typing import Any, Dict, Protocol


class EmitProtocol(Protocol):
    """Protocol exposing the emit method."""

    def emit(self, selector: str, data: Dict[str, Any]) -> None:
        """Sends a message to all listening agents on the specified selector.

        Args:
            selector: target selector.
            data: message data to be serialized.
        Raises:
            NonListedMessageSelectorError: when selector is not part of listed out selectors.

        Returns:
            None
        """
        pass
