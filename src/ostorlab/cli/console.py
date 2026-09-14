"""Pretty prints and logs console statements."""

import logging
from typing import Any, ClassVar

import rich
from rich import box, markup, status


def _escape(text: Any, is_markup: bool) -> str:
    """Escapes rich markup control characters from dynamic text.

    Rich interprets square brackets as markup tags, which raises a `MarkupError` for text holding
    unbalanced brackets, like regular expressions, URLs or asset representations.

    Args:
        text: The text to render, not necessarily a string.
        is_markup: Whether the text is trusted to hold intentional rich markup.

    Returns:
        The text, escaped unless it is trusted markup.
    """
    if is_markup is True:
        return str(text)
    return markup.escape(str(text))


def _escape_cell(value: Any) -> Any:
    """Escapes a table cell, leaving rich renderables, like `Text` or `Markdown`, untouched.

    Args:
        value: The cell value, either a string or a rich renderable.

    Returns:
        The cell value, escaped if it is a string.
    """
    if isinstance(value, str) is False:
        return value
    return _escape(value, is_markup=False)


class Console:
    """Pretty prints and logs console statements."""

    THEME: ClassVar[dict[str, str]] = {
        "success": "bold green",
        "error": "red",
        "warning": "yellow",
        "info": "bold blue",
    }

    def __init__(
        self,
        theme: dict[str, str] | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initializes the console with text styling.

        Args:
            theme: The text styling. Defaults to None.
        """
        if theme is None:
            theme = self.THEME
        self._console = rich.console.Console(theme=rich.theme.Theme(theme))
        self._table = rich.table.Table
        self._logger = logger

    def success(self, text: str, is_markup: bool = False) -> None:
        """Shows success message.

        Args:
            text: The success text to show.
            is_markup: Whether the text holds intentional rich markup. Defaults to False.
        """
        self._console.print(
            f":heavy_check_mark: {_escape(text, is_markup)}", style="success"
        )
        if self._logger is not None:
            self._logger.info(text)

    def error(self, text: str, is_markup: bool = False) -> None:
        """Shows error message.

        Args:
            text: The error text to show.
            is_markup: Whether the text holds intentional rich markup. Defaults to False.
        """
        self._console.print(
            f":small_red_triangle: [bold]ERROR:[/] {_escape(text, is_markup)}",
            style="error",
        )
        if self._logger is not None:
            self._logger.error(text)

    def warning(self, text: str, is_markup: bool = False) -> None:
        """Shows warning message.

        Args:
            text: The warning text to show.
            is_markup: Whether the text holds intentional rich markup. Defaults to False.
        """
        self._console.print(
            f":small_orange_diamond: [bold]WARNING:[/] {_escape(text, is_markup)}",
            style="warning",
        )
        if self._logger is not None:
            self._logger.warning(text)

    def info(self, text: str, is_markup: bool = False) -> None:
        """Shows general information message.

        Args:
            text: The general text to show.
            is_markup: Whether the text holds intentional rich markup. Defaults to False.
        """
        self._console.print(f":small_blue_diamond: {_escape(text, is_markup)}")
        if self._logger is not None:
            self._logger.info(text)

    def status(self, text: str, is_markup: bool = False) -> status.Status:
        """Shows loading text.

        Args:
            text: The loading text to show.
            is_markup: Whether the text holds intentional rich markup. Defaults to False.

        Returns:
            The loading text.
        """
        return self._console.status(f"[info]{_escape(text, is_markup)}")

    def table(
        self, columns: dict[str, str], data: list[dict[str, Any]], title: str
    ) -> None:
        """Constructs a table to display a list of items.

        String cells are escaped, as they hold untrusted values like asset URLs. Styled cells must
        be passed as rich renderables, `Text` or `Markdown`, which are rendered as they are.

        Args:
            columns: The table columns.
            data: The list of items to display.
            title: The title of the table.
        """

        table = self._table(title=f"\n[bold]{_escape(title, False)}", show_lines=True)

        for column in columns:
            table.add_column(_escape(column, False))

        for item in data:
            row_values = []
            for column in columns.values():
                row_values.append(_escape_cell(item[column]))
            table.add_row(*row_values)

        table.box = box.SQUARE_DOUBLE_HEAD
        self._console.print(table)

    def print(self, data: Any) -> None:
        self._console.print(data)
