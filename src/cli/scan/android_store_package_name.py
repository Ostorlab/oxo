import logging

from cli.rootcli import scan

logger = logging.getLogger(__name__)


@scan.command()
def android_store():
    """Command on cli1"""
