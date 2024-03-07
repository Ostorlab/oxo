"""Module for the command run inside the group scan.
This module takes care of preparing the selected runtime and the lists of provided agents, before starting a scan.
Example of usage:
    - ostorlab scan run --agent=agent1 --agent=agent2 --title=test_scan [asset] [options]."""

import io
import logging

import httpx
from typing import List

import click
from ruamel.yaml import error

from ostorlab import exceptions
from ostorlab.agent.schema import validator
from ostorlab.cli import console as cli_console
from ostorlab.cli import install_agent
from ostorlab.cli.scan import scan
from ostorlab.cli import types
from ostorlab.cli import agent_fetcher
from ostorlab.runtimes import definitions
from ostorlab.runtimes import runtime
from ostorlab.utils import defintions as utils_definitions

console = cli_console.Console()

logger = logging.getLogger(__name__)


@scan.group(invoke_without_command=True)
@click.option(
    "--agent",
    multiple=True,
    help="List of agents keys. to use in the scan.",
    required=False,
)
@click.option(
    "--arg",
    multiple=True,
    help="""Add an argument to an agent. The argument should be in the format: <name>:<value>.
     Example: --arg fast_mode:true
    """,
    type=types.AgentArgType(),
    required=False,
)
@click.option("--title", "-t", help="Scan title.")
@click.option(
    "--agent-group-definition",
    "-g",
    type=click.File("r"),
    help="Path to agents group definition file (yaml).",
    required=False,
)
@click.option(
    "--assets",
    "-a",
    type=click.File("r"),
    help="Path to target list definition file (yaml).",
    required=False,
)
@click.option(
    "--install", "-i", help="Install missing agents.", is_flag=True, required=False
)
@click.option(
    "--follow",
    help="Follow logs of provided list of agents and services.",
    multiple=True,
    default=[],
)
@click.option(
    "--no-asset",
    help="Start the environment without injecting assets",
    is_flag=True,
    required=False,
)
@click.pass_context
def run(
    ctx: click.core.Context,
    agent: List[str],
    arg: list[types.AgentArg],
    agent_group_definition: io.FileIO,
    assets: io.FileIO,
    title: str,
    install: bool,
    follow: List[str],
    no_asset: bool,
) -> None:
    """Start a new scan on your assets.\n
    Example:\n
        - ostorlab scan run --agent=agent/ostorlab/nmap --agent=agent/google/tsunami --title=test_scan ip 8.8.8.8
    """
    if no_asset is True and ctx.invoked_subcommand is not None:
        console.error(
            f"Sub-command {ctx.invoked_subcommand} specified with --no-asset flag."
        )
        raise click.exceptions.Exit(2)
    if no_asset is False and ctx.invoked_subcommand is None and assets is None:
        console.error("Error: Missing command.")
        click.echo(ctx.get_help())
        raise click.exceptions.Exit(2)

    if agent:
        agents_settings: List[definitions.AgentSettings] = []
        for agent_key in agent:
            agents_settings.append(definitions.AgentSettings(key=agent_key))

        agent_group = definitions.AgentGroupDefinition(agents=agents_settings)
    elif agent_group_definition:
        try:
            agent_group = definitions.AgentGroupDefinition.from_yaml(
                agent_group_definition
            )
        except validator.ValidationError as e:
            console.error("Invalid agent group definition.")
            console.print(f"{e}")
            raise click.exceptions.Exit(2)
        except error.YAMLError as e:
            console.error("Agent group definition YAML parse error:")
            console.print(f"{e}")
            raise click.exceptions.Exit(2)
    else:
        raise click.ClickException("Missing agent list or agent group definition.")

    asset_group = None
    if assets is not None:
        try:
            asset_group = definitions.AssetsDefinition.from_yaml(assets)
        except validator.ValidationError as e:
            console.error(f"{e}")
            raise click.ClickException("Invalid asset Group Definition.") from e
    runtime_instance: runtime.Runtime = ctx.obj["runtime"]
    # set list of log follow.
    runtime_instance.follow = follow
    try:
        can_run_scan = runtime_instance.can_run(agent_group_definition=agent_group)
    except exceptions.OstorlabError as e:
        console.error(f"{e}")
        raise click.ClickException("Runtime encountered an error to run scan") from e

    if can_run_scan is True:
        ctx.obj["agent_group_definition"] = agent_group
        ctx.obj["title"] = title
        if install is True:
            try:
                # Trigger both the runtime installation routine and install all the provided agents.
                runtime_instance.install()
                for ag in agent_group.agents:
                    try:
                        install_agent.install(ag.key, ag.version)
                    except agent_fetcher.AgentDetailsNotFound:
                        console.warning(f"agent {ag.key} not found on the store")
            except httpx.HTTPError as e:
                raise click.ClickException(f"Could not install the agents: {e}")
        if arg is not None and len(arg) > 0:
            agent_group.agents = _add_cli_args_to_agent_settings(
                agent_group.agents, cli_args=arg
            )
        if ctx.invoked_subcommand is None:
            runtime_instance.scan(
                title=ctx.obj["title"],
                agent_group_definition=ctx.obj["agent_group_definition"],
                assets=asset_group if asset_group is None else asset_group.targets,
            )
    else:
        raise click.ClickException(
            "The runtime does not support the provided agent list or group definition."
        )


def _add_cli_args_to_agent_settings(
    agents_settings: list[definitions.AgentSettings], cli_args: list[types.AgentArg]
) -> list[definitions.AgentSettings]:
    """
    Adds CLI arguments to the agent settings if they are supported by the agent.

    Args:
        agents_settings : A list of agent settings.
        cli_args : A list of CLI Agent arguments.

    Returns:
         The updated list of agent settings.

    Raises:
        click.exceptions.Exit: If agent details are not found.
    """
    for agent_setting in agents_settings:
        try:
            agent_definition = agent_fetcher.get_definition(agent_setting.key)
        except agent_fetcher.AgentDetailsNotFound:
            console.error(f"Agent {agent_setting.key} not found.")
            raise click.exceptions.Exit(2)

        for cli_argument in cli_args:
            for arg in agent_definition.args:
                if arg.get("name") == cli_argument.name:
                    try:
                        agent_setting.args.append(
                            utils_definitions.Arg.build(
                                name=cli_argument.name,
                                type=arg.get("type", "string"),
                                value=cli_argument.value,
                            )
                        )
                        break
                    except ValueError as e:
                        console.warning(
                            f"Could not set argument {cli_argument.name} to {cli_argument.value} because of "
                            f"the following error: {e}"
                        )
    return agents_settings
