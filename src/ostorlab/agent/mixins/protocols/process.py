"""Definition of the emitting protocol exposing the process(s) method."""
from typing import Protocol


class ProcessProtocol(Protocol):

    name: str

    def process_message(self, selector: str, message: bytes) -> None:
        """Processes raw message received from BS.

        Args:
            selector: destination selector with full path, including UUID set by default.
            message: raw bytes message.

        Returns:
            None
        """
        pass