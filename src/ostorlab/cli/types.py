"""This module contains custom types for the CLI commands."""

import dataclasses
from typing import Optional

import click

OSTORLAB_AGENTS_PREFIX = "agent/ostorlab"


@dataclasses.dataclass
class AgentArg:
    """Dataclass representing an agent argument passed from cli."""

    name: str
    value: str


class AgentArgType(click.ParamType):
    """Custom Click type for parsing agent arguments in the format 'arg_name:arg_value'."""

    name = "arg_name:arg_value"

    def convert(
        self,
        arg_value: str,
        param: Optional[click.Parameter],
        ctx: Optional[click.Context],
    ) -> AgentArg:
        """Override convert method from ParamType class to parse command line arguments of agents in the format
        'arg_name:arg_value' and convert them into AgentArg objects.

        Args:
            arg_value: The argument value in the format `arg_name:arg_value`.
            param: The parameter using this type for conversion. Defaults to None.
            ctx: The current click context. Defaults to None.

        Returns:
            AgentArg: An AgentArg object representing the parsed argument.

        Raises:
            click.BadParameter: If the argument value cannot be parsed into the expected format.
        """
        try:
            arg_name, arg_value = arg_value.split(":")
            return AgentArg(name=arg_name, value=arg_value)
        except ValueError:
            self.fail(
                message=f"Invalid argument {arg_value}. The expected format is name:value. Example: --arg "
                f"fast_mode:false",
                param=param,
                ctx=ctx,
            )


class AgentKeyType(click.ParamType):
    """Custom Click type for parsing agent keys."""

    name = "agent_key"

    def convert(
        self,
        cli_value: str,
        param: Optional[click.Parameter],
        ctx: Optional[click.Context],
    ) -> str:
        """Override convert method from ParamType class to parse agent keys and convert them into the right key if
        applicable.

        Args:
            cli_value: The cli value for agent key.
            param: The parameter using this type for conversion. Defaults to None.
            ctx: The current click context. Defaults to None.

        Returns:
            str: The agent key.

        Raises:
            click.BadParameter: If the agent key is malformed.
        """
        forward_slash_count = cli_value.count("/")
        if forward_slash_count == 0:
            return f"{OSTORLAB_AGENTS_PREFIX}/{cli_value}"
        elif forward_slash_count == 1 and cli_value.startswith("@") is True:
            return f"agent/{cli_value[1:]}"
        elif forward_slash_count == 2:
            return cli_value
        else:
            self.fail(
                message=f"Invalid agent key: {cli_value}. The expected formats are:  (agent/<org>/<name> or "
                f"@<org>/<name>). Org name can be omitted for defaults agent hosted by Ostorlab.",
                param=param,
                ctx=ctx,
            )
