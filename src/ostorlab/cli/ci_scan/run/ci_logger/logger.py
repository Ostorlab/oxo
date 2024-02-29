"""Logger is in charge of defining the output format based on CI expected output."""

import abc


class Logger(abc.ABC):
    """Logger is in charge of printing the results based on the CI expected output."""

    @abc.abstractmethod
    def info(self, message: str) -> None:
        """Print Info messages.

        Args:
            message: message to print.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def error(self, message: str) -> None:
        """Print Error messages.

        Args:
            message: message to print.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def output(self, name: str, value: str) -> None:
        """Pass an output to the next step of the CI.

        Args:
            name: name of the output to pass to the next step.
            value: value of the output.
        """
        raise NotImplementedError()
