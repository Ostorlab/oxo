"""Module for the root command: auth."""

from ostorlab.cli.auth import auth
from ostorlab.cli.auth import login
from ostorlab.cli.auth import revoke

__all__ = ["auth", "login", "revoke"]
