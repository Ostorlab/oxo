"""This module contains custom types for the CLI commands."""

import logging
import dataclasses
from typing import Union

from ostorlab.cli import console as cli_console
import click

console = cli_console.Console()

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class AgentArg:
    name: str
    value: Union[str, list[str]] | None = None


class AgentArgType(click.ParamType):
    name = "agent_arg"

    def convert(
        self, arg_value: str, param: click.Parameter | None, ctx: click.Context | None
    ) -> AgentArg:
        try:
            arg_name, arg_value = arg_value.split(":")
            if len(arg_value.split(",")) > 1:
                return AgentArg(name=arg_name, value=arg_value.split(","))
            else:
                return AgentArg(name=arg_name, value=arg_value)
        except ValueError:
            self.fail(
                message=f"Invalid argument {arg_value}. Expected format: name:value. where value can be a string or "
                f"an array of strings. Example: ports:80,443,8080",
                param=param,
                ctx=ctx,
            )
