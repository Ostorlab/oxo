"""Pretty prints and logs console statements."""

import rich
from dateutil import parser
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
        self._table = rich.table.Table

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

    def format_date(self, date: str) -> str:
        """Formats date to a readable format.

        Args:
            date: The date to format.

        Returns:
            The formatted date.
        """
        parsed_date = parser.parse(date)
        return parsed_date.strftime('%B %d %Y')

    def scan_list_table(self, data) -> None:
        """Constructs a table to display the list of scans.

        Args:
            data: The list of scans and other meta data such as
            count and number of pages.
        """
        scans = data['data']['scans']['scans']
        scans_table = self._table(
            title=f'\n[bold]Showing {len(scans)} Scans', show_lines=True)

        scans_table.add_column('Application')
        scans_table.add_column('Platform')
        scans_table.add_column('Plan')
        scans_table.add_column('Created Time')
        scans_table.add_column('Progress')
        scans_table.add_column('Risk')

        for scan in scans:
            scans_table.add_row(f'{scan["packageName"]}:{scan["version"]}', scan['assetType'],
                                scan['plan'], self.format_date(scan['createdTime']),
                                scan['progress'], scan['riskRating'])

        self._console.print(scans_table)
