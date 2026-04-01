"""Asset of type Message.
This module takes care of preparing an arbitrary protobuf message
to be injected onto the message bus."""

import logging

import click
from google.protobuf import text_format

from ostorlab.agent.message import serializer
from ostorlab.assets import message as message_asset
from ostorlab.cli import console as cli_console
from ostorlab.cli.scan.run import run
from ostorlab import exceptions

logger = logging.getLogger(__name__)
console = cli_console.Console()


@run.run.command(name="message")
@click.option(
    "--selector",
    required=True,
    help="Message selector (e.g., v3.report.risk).",
)
@click.option(
    "--textproto",
    "proto_file",
    required=True,
    type=click.Path(exists=True),
    help="Path to a proto text format file.",
)
@click.pass_context
def message_cli(
    ctx: click.core.Context,
    selector: str,
    proto_file: str,
) -> None:
    """Run scan with an arbitrary protobuf message injected onto the message bus.\n
    Example:\n
        - oxo scan run --agent=agent/ostorlab/nebula message --selector "v3.report.risk" --textproto risk.textproto
    """
    try:
        proto_class = serializer.find_proto_class(selector)
    except serializer.SerializationError as e:
        console.error(f"Could not find proto definition for selector '{selector}': {e}")
        raise click.exceptions.Exit(2)

    proto_message = proto_class()

    with open(proto_file, "r") as f:
        file_content = f.read()

    try:
        text_format.Parse(file_content, proto_message)
    except text_format.ParseError as e:
        console.error(f"Failed to parse proto text file: {e}")
        raise click.exceptions.Exit(2)

    proto_bytes = proto_message.SerializeToString()
    if proto_bytes == b"":
        console.error(
            "Proto text file produced an empty message. "
            "Check that field names match the selector's proto definition."
        )
        raise click.exceptions.Exit(2)

    runtime = ctx.obj["runtime"]
    assets = [message_asset.Message(selector=selector, proto_bytes=proto_bytes)]

    logger.debug("injecting message asset %s", assets)
    try:
        created_scan = runtime.scan(
            title=ctx.obj["title"],
            agent_group_definition=ctx.obj["agent_group_definition"],
            assets=assets,
        )
        if created_scan is not None:
            runtime.link_agent_group_scan(
                created_scan, ctx.obj["agent_group_definition"]
            )
            runtime.link_assets_scan(created_scan.id, assets)

    except exceptions.OstorlabError as e:
        console.error(f"An error was encountered while running the scan: {e}")
