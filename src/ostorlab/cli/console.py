"""Utils to pretty print console statements."""

import rich

custom_theme = rich.theme.Theme({
    'success': 'bold green',
    'error': 'red',
    'warning': 'yellow',
    'info': 'bold blue'
})

console = rich.console.Console(theme=custom_theme)


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

