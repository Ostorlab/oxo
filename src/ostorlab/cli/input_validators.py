"""Module offering methods to validate CLI user input."""

import re

import click


def validate_port_binding_input(ctx: click.core.Context, param: str, value: str) -> str:
    """Validator for the bind ports flag.
    Input should be as follows: service_port1:host_port1,service_port2:host_port2

    Args:
        ctx: as per click callback convention, the calling click context.
        param: as per click callback convention: the parameter name of argument.
        value: value of the argument.
    """
    del ctx, param
    if value is not None and not re.match(r"^\d+:\d+(,\d+:\d+)?$", value):
        raise click.UsageError(
            "Incorrect port binding syntax: service_port1:host_port1,service_port2:host_port2"
        )
    else:
        return value
