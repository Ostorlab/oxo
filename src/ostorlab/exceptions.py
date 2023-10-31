"""This module contains the set of Ostorlab exceptions."""


class OstorlabError(Exception):
    """Ostorlab base error that all the exceptions inherit from."""


class ArgumentMissingInAgentDefinitionError(OstorlabError):
    """Argument is present in the settings but not in the agent definition."""
