"""This module contains custom types for the CLI commands."""

import dataclasses
from typing import Optional

import click


@dataclasses.dataclass
class AgentArg:
    name: str
    value: str


class AgentArgType(click.ParamType):
    name = "agent_arg"

    def convert(
        self,
        arg_value: str,
        param: Optional[click.Parameter],
        ctx: Optional[click.Context],
    ) -> AgentArg:
        try:
            arg_name, arg_value = arg_value.split("=")
            return AgentArg(name=arg_name, value=arg_value)
        except ValueError:
            self.fail(
                message=f"Invalid argument {arg_value}. The expected format is name=value. Example: --arg "
                f"fast_mode=false",
                param=param,
                ctx=ctx,
            )
