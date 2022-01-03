"""Utils to pretty print console statements."""

import time
from rich import theme
from rich import console
from rich import progress

custom_theme = theme.Theme({
    'success': 'bold green',
    'error': 'red',
    'warning': 'yellow',
    'info': 'bold blue'
})

progress = progress.Progress()
console = console.Console(theme=custom_theme)


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
    return console.print(info_text, style="info")


def authenticate():
    """Shows a message for each step in authentication."""

    console.print()

    with console.status(status='[bold blue]Logging you into Ostorlab') as status:
        time.sleep(3)
        status.update(status='[bold blue]Validating your credentials')
        time.sleep(3)
        status.update(status='[bold blue]Logging into your account')
        time.sleep(3)
        status.update(status='[bold blue]Generating your API key')
        time.sleep(2)
        status.update(status='[bold blue]Persisting your API key')
        time.sleep(3)
    console.print('[bold green]Authentication successful')


def processing():
    """Shows text when any command is entered."""
    console.print()

    with console.status('[green]Processing request...'):
        time.sleep(1.5)
        console.log('[bold]Request processed.')
