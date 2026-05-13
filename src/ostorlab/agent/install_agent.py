"""Shared entrypoint for installing an agent image.

Re-exports the install logic from the CLI module so non-CLI consumers
(e.g. the scanner runtime) do not need to import from the presentation layer.
"""

from ostorlab.cli.install_agent import install

__all__ = ["install"]
