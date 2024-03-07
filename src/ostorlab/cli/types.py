"""This module contains custom types for the CLI commands."""

import dataclasses
from typing import Optional

import click


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
