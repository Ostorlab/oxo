"""Asset of type ticket for scanning."""

import logging
from typing import Optional

import click

from ostorlab.assets import ticket as ticket_asset
from ostorlab.cli.scan.run import run
from ostorlab import exceptions
from ostorlab.cli import console as cli_console

console = cli_console.Console()
logger = logging.getLogger(__name__)


@run.run.command()
@click.option("--title", help="Ticket title.", required=True)
@click.option("--ticket-id", help="Ticket ID.", required=False)
@click.option("--description", help="Ticket description.", required=True)
@click.option(
    "--comment",
    "comments",
    help="Ticket comments in the format author:message.",
    required=False,
    multiple=True,
)
@click.pass_context
def ticket(
    ctx: click.core.Context,
    title: str,
    description: str,
    ticket_id: Optional[str] = None,
    comments: Optional[list[str]] = None,
) -> None:
    """Run scan for ticket."""
    runtime = ctx.obj["runtime"]
    parsed_comments = []
    if comments is not None and len(comments) > 0:
        for comment in comments:
            if ":" in comment:
                author, message = comment.split(":", 1)
                parsed_comments.append(
                    ticket_asset.Comment(author=author, message=message)
                )
            else:
                parsed_comments.append(ticket_asset.Comment(message=comment))

    asset = ticket_asset.Ticket(
        title=title,
        description=description,
        ticket_id=ticket_id,
        comments=parsed_comments,
    )
    logger.debug("scanning asset %s", asset)
    try:
        runtime.scan(
            title=ctx.obj["title"],
            agent_group_definition=ctx.obj["agent_group_definition"],
            assets=[asset],
        )
    except exceptions.OstorlabError as e:
        console.error(f"An error was encountered while running the scan: {e}")
