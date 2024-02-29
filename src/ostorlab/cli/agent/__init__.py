"""Module for the root command: agent."""

from ostorlab.cli.agent.agent import agent
from ostorlab.cli.agent import build
from ostorlab.cli.agent import install
from ostorlab.cli.agent import healthcheck
from ostorlab.cli.agent import delete
from ostorlab.cli.agent import list as list_cli
from ostorlab.cli.agent import search as search_cli

__all__ = [
    "agent",
    "build",
    "install",
    "healthcheck",
    "delete",
    "list_cli",
    "search_cli",
]
