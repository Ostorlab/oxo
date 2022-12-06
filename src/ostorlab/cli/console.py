"""Pretty prints and logs console statements."""

from typing import Dict, List

import rich
from rich import box
from rich import status


class Console:
    """Pretty prints and logs console statements."""

    THEME = {
        "success": "bold green",
        "error": "red",
        "warning": "yellow",
        "info": "bold blue",
    }

    def __init__(self, theme: Dict[str, str] = None) -> None:
        """Initializes the console with text styling.

        Args:
            theme: The text styling. Defaults to None.
        """
        if theme is None:
            theme = self.THEME
        self._console = rich.console.Console(theme=rich.theme.Theme(theme))
        self._table = rich.table.Table

    def success(self, text: str) -> None:
        """Shows success message.

        Args:
            text: The success text to show.
        """
        self._console.print(f":heavy_check_mark: {text}", style="success")

    def error(self, text: str) -> None:
        """Shows error message.

        Args:
            text: The error text to show.
        """
        self._console.print(
            f":small_red_triangle: [bold]ERROR:[/] {text}", style="error"
        )

    def warning(self, text: str) -> None:
        """Shows warning message.

        Args:
            text: The warning text to show.
        """
        self._console.print(
            f":small_orange_diamond: [bold]WARNING:[/] {text}", style="warning"
        )

    def info(self, text: str) -> None:
        """Shows general information message.

        Args:
            text: The general text to show.
        """
        self._console.print(f":small_blue_diamond: {text}")

    def status(self, text: str) -> status.Status:
        """Shows loading text.

        Args:
            text: The loading text to show.

        Returns:
            The loading text.
        """
        return self._console.status(f"[info]{text}")

    def table(self, columns: Dict[str, str], data: List[Dict], title: str) -> None:
        """Constructs a table to display a list of items.

        Args:
            columns: The table columns.
            data: The list of items to display.
            title: The title of the table.
        """

        table = self._table(title=f"\n[bold]{title}", show_lines=True)

        for column in columns.keys():
            table.add_column(column)

        for item in data:
            row_values = []
            for column in columns.values():
                row_values.append(item[column])
            table.add_row(*row_values)

        table.box = box.SQUARE_DOUBLE_HEAD
        self._console.print(table)

    def print(self, data):
        self._console.print(data)
