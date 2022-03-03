"""Logger is in charge of definning the output format based on CI expected output."""
from ostorlab.cli import console as cli_console
from ostorlab.cli.ci_scan.run.ci_logger import logger

console = cli_console.Console()


class Logger(logger.Logger):
    """Logger is in charge of printing the results based on the CI expected output."""

    def info(self, message: str) -> None:
        """Print Info messages.

        Args:
            message: message to print.
        """
        console.info(message)

    def error(self, message: str) -> None:
        """Print Error messages.

        Args:
            message: message to print.
        """
        console.error(message)

    def output(self, name: str, value: str) -> None:
        """Pass an output to the next step of the CI.

        Args:
            name: name of the output to pass to the next step.
            value: value of the output.
        """
        print(f'::set-output name={name}::{value}')
