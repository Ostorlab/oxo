import logging

from cli.rootcli import scan

logger = logging.getLogger(__name__)


@scan.command()
def web():
    """Command on cli1"""
