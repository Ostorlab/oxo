"""Vulnz module that handles listing and describing a vulnerability."""
from ostorlab.cli.rootcli import rootcli


@rootcli.group()
def vulnz() -> None:
    """You can use vulnz to list and describe vulnerabilities.\n"""
    pass
