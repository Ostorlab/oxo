"""Asset of type repository.
This module prepares a source code repository asset before injecting it to the runtime."""

import logging

import click

from ostorlab.assets import repository as repository_asset
from ostorlab.cli import console as cli_console
from ostorlab.cli.scan.run import run
from ostorlab import exceptions

console = cli_console.Console()
logger = logging.getLogger(__name__)


@run.run.command(name="repository")
@click.option("--repository-url", "--origin-url")
@click.option("--commit-hash")
@click.option(
    "--provider",
    type=click.Choice(
        ["github", "gitlab", "azure", "bitbucket", "git"],
        case_sensitive=False,
    ),
)
@click.option("--content-url")
@click.pass_context
def repository_cli(
    ctx: click.core.Context,
    repository_url: str | None,
    commit_hash: str | None,
    provider: str | None,
    content_url: str | None,
) -> None:
    """Run scan for a source code repository asset.

    A repository is defined either with the git fields (--repository-url,
    --commit-hash and --provider together) or with --content-url pointing to a
    source archive, but not both.
    """
    git_fields = (repository_url, commit_hash, provider)
    is_git = any(field is not None for field in git_fields)

    if is_git is True and content_url is not None:
        raise click.UsageError(
            "Provide either the git fields (--repository-url, --commit-hash, "
            "--provider) or --content-url, not both."
        )
    if is_git is False and content_url is None:
        raise click.UsageError(
            "A repository requires either the git fields (--repository-url, "
            "--commit-hash, --provider) or --content-url."
        )
    if is_git is True and all(field is not None for field in git_fields) is False:
        raise click.UsageError(
            "--repository-url, --commit-hash and --provider must be provided together."
        )

    assets = [
        repository_asset.Repository(
            repository_url=repository_url or "",
            commit_hash=commit_hash or "",
            provider=provider.upper() if provider is not None else "",
            content_url=content_url or "",
        )
    ]

    logger.debug("scanning assets %s", [str(a) for a in assets])
    runtime = ctx.obj["runtime"]
    try:
        runtime.scan(
            title=ctx.obj["title"],
            agent_group_definition=ctx.obj["agent_group_definition"],
            assets=assets,
        )
    except exceptions.OstorlabError as e:
        console.error(f"An error was encountered while running the scan: {e}")
