"""ci_scan module that handles running a scan on the CI."""
from ostorlab.cli.rootcli import rootcli


@rootcli.group()
def ci_scan() -> None:
    """You can use ci_scan to run scan on the CI.\n"""
    pass
