"""Utils to pretty print console statements."""

import time
from rich import theme
from rich import console
from rich import progress

custom_theme = theme.Theme({
   "success": "bold green",
   "error": "red",
   "warning": "yellow",
   "info": "bold blue"
})

console = console.Console(theme=custom_theme)

def success(success_text: str):
   return console.print(success_text, style="success")


def error(error_text: str):
   return console.print(f'[bold]ERROR:[/] {error_text}', style="error")


def warning(warning_text: str):
   return console.print(f'[bold]WARNING:[/] {warning_text}', style="warning")


def info(info_text: str):
   return console.print(info_text, style="info")

def auth():
   with progre as progress:

    task1 = progress.add_task("[red]Downloading...", total=1000)
    task2 = progress.add_task("[green]Processing...", total=1000)
    task3 = progress.add_task("[cyan]Cooking...", total=1000)

    while not progress.finished:
        progress.update(task1, advance=0.5)
        progress.update(task2, advance=0.3)
        progress.update(task3, advance=0.9)
        time.sleep(0.02)
