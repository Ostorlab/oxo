"""Ostorlab main package."""

import logging

import click
from ostorlab.cli.rootcli import rootcli
from rich import console
from rich import logging as rich_logging

FORMAT = "%(message)s"
logging.basicConfig(
    level="ERROR",
    format=FORMAT,
    datefmt="[%X]",
    handlers=[
        rich_logging.RichHandler(
            rich_tracebacks=True,
            console=console.Console(width=255),
            tracebacks_suppress=[click],
        )
    ],
)

logger = logging.getLogger("CLI")


def main():
    rootcli(None)
