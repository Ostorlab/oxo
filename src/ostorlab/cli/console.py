"""Pretty prints and logs console statements."""

import rich
from rich import status
from typing import Dict


class Console():
    """Pretty prints and logs console statements."""

    THEME = {
        'success': 'bold green',
        'error': 'red',
        'warning': 'yellow',
        'info': 'bold blue'
    }

    def __init__(self, theme: Dict[str, str] = None) -> None:
        """Initializes the console with text styling.

        Args:
            theme: The text styling. Defaults to None.
        """
        if theme is None:
            theme = self.THEME
        self._console = rich.console.Console(theme=rich.theme.Theme(theme))

    def success(self, success_text: str) -> None:
        """Shows success message.

        Args:
            success_text: The success text to show.
        """
        self._console.print(success_text, style='success')


    def error(self, error_text: str) -> None:
        """Shows error message.

        Args:
            error_text: The error text to show.
        """
        self._console.print(f'[bold]ERROR:[/] {error_text}', style='error')


    def warning(self, warning_text: str) -> None:
        """Shows warning message.

        Args:
            warning_text: The warning text to show.
        """
        self._console.print(f'[bold]WARNING:[/] {warning_text}', style='warning')


    def info(self, info_text: str) -> None:
        """Shows general information message.

        Args:
            info_text: The general text to show.
        """
        self._console.print(info_text, style='info')

    def status(self, status_text: str) -> status.Status:
        """Shows loading text.

        Args:
            status_text: The loading text to show.

        Returns:
            The loading text.
        """
        return self._console.status(f'[info]{status_text}')

