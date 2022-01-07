"""Ostorlab main package."""
import logging
from rich.logging import RichHandler
from ostorlab.cli.rootcli import rootcli

FORMAT = '%(message)s'
logging.basicConfig(
    level='ERROR', format=FORMAT, datefmt='[%X]', handlers=[RichHandler(rich_tracebacks=True)]
)

logger = logging.getLogger('CLI')


def main():
    rootcli(None)
