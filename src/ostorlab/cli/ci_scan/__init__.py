"""Module for the root command ci_scan"""

# ruff: noqa: I001 - import order required to avoid circular imports
from ostorlab.cli.ci_scan.ci_scan import ci_scan
from ostorlab.cli.ci_scan import run

__all__ = ["ci_scan", "run"]
