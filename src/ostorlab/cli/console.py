"""Utils to pretty print console statements."""

import rich

custom_theme = rich.theme.Theme({
    'success': 'bold green',
    'error': 'red',
    'warning': 'yellow',
    'info': 'bold blue'
})

console = rich.console.Console(theme=custom_theme)
table = rich.table.Table


def success(success_text: str):
    """Shows success message.

    Args:
        success_text: success message to show.

    Returns:
       # TODO (Rabson) add return type
    """
    return console.print(success_text, style='success')


def error(error_text: str):
    """Shows error message.

    Args:
        error_text: error message to show.

    Returns:
       # TODO (Rabson) add return type
    """
    return console.print(f'[bold]ERROR:[/] {error_text}', style='error')


def warning(warning_text: str):
    """Shows warning message.

     Args:
         warning_text: warning message to show.

     Returns:
        # TODO (Rabson) add return type
     """
    return console.print(f'[bold]WARNING:[/] {warning_text}', style='warning')


def info(info_text: str):
    """Shows general information message.

      Args:
          info_text: general information message to show.

      Returns:
         # TODO (Rabson) add return type
      """
    return console.print(info_text, style='info')


def print_json_data(data) -> None:
    """pretty prints a dictionary.

    Args:
        data: The data to pretty print.
    """
    rich.print_json(data=data)


def scan_list_table(data) -> None:
    """Constructs a table to display the list of scans.

    Args:
        data: The list of scans and other meta data such as
        count and number of pages.
    """
    scans = data['data']['scans']['scans']
    scans_table = table(title=f'\n[bold]Showing {len(scans)} Scans', show_lines=True)

    scans_table.add_column('Application')
    scans_table.add_column('Platform')
    scans_table.add_column('Plan')
    scans_table.add_column('Created Time')
    scans_table.add_column('Progress')
    scans_table.add_column('Risk')

    for scan in scans:
        scans_table.add_row(f'{scan["packageName"]}:{scan["version"]}', scan['assetType'],
                            scan['plan'], scan['createdTime'], scan['progress'], scan['riskRating'])

    console.print(scans_table)

