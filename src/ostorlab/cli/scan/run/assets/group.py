"""Asset of type multi-asset group.
This module prepares a heterogeneous group of assets (mobile packages, domains,
links, repositories, API schemas and files) before injecting them to the runtime
instance in a single scan.
"""

import logging

import click

from ostorlab.assets import android_apk as android_apk_asset
from ostorlab.assets import api_schema as api_schema_asset
from ostorlab.assets import asset as asset_lib
from ostorlab.assets import domain_name as domain_name_asset
from ostorlab.assets import file as file_asset
from ostorlab.assets import harmonyos_hap as harmonyos_hap_asset
from ostorlab.assets import ios_ipa as ios_ipa_asset
from ostorlab.assets import link as link_asset
from ostorlab.assets import repository as repository_asset
from ostorlab.cli import console as cli_console
from ostorlab.cli.scan.run import run
from ostorlab import exceptions

console = cli_console.Console()
logger = logging.getLogger(__name__)


@run.run.command(name="group")
@click.option("--apk", "apk", multiple=True, help="Source URL of an Android .APK.")
@click.option("--ipa", "ipa", multiple=True, help="Source URL of an iOS .IPA.")
@click.option(
    "--harmony-hap",
    "harmony_hap",
    multiple=True,
    help="Source URL of a HarmonyOS .HAP.",
)
@click.option("--domain", "domain", multiple=True, help="Domain name to scan.")
@click.option("--link", "link", multiple=True, help="URL of a link to scan.")
@click.option(
    "--link-method",
    "link_method",
    multiple=True,
    help="HTTP method of the corresponding --link (defaults to GET).",
)
@click.option("--repository-url", "repository_url", multiple=True)
@click.option("--repository-commit-hash", "repository_commit_hash", multiple=True)
@click.option("--repository-provider", "repository_provider", multiple=True)
@click.option("--api-schema-endpoint", "api_schema_endpoint", multiple=True)
@click.option("--api-schema-url", "api_schema_url", multiple=True)
@click.option("--api-schema-type", "api_schema_type", multiple=True)
@click.option("--file", "file", multiple=True, help="Source URL of a generic file.")
@click.pass_context
def group_cli(
    ctx: click.core.Context,
    apk: tuple[str, ...],
    ipa: tuple[str, ...],
    harmony_hap: tuple[str, ...],
    domain: tuple[str, ...],
    link: tuple[str, ...],
    link_method: tuple[str, ...],
    repository_url: tuple[str, ...],
    repository_commit_hash: tuple[str, ...],
    repository_provider: tuple[str, ...],
    api_schema_endpoint: tuple[str, ...],
    api_schema_url: tuple[str, ...],
    api_schema_type: tuple[str, ...],
    file: tuple[str, ...],
) -> None:
    """Run a single scan on a heterogeneous group of assets.\n
    Example:\n
        - oxo scan run -g group.yaml group --apk https://cdn/app.apk --ipa https://cdn/app.ipa \
--domain example.com --link https://app.example.com --link-method GET
    """
    runtime = ctx.obj["runtime"]

    assets = _build_assets(
        apk=apk,
        ipa=ipa,
        harmony_hap=harmony_hap,
        domain=domain,
        link=link,
        link_method=link_method,
        repository_url=repository_url,
        repository_commit_hash=repository_commit_hash,
        repository_provider=repository_provider,
        api_schema_endpoint=api_schema_endpoint,
        api_schema_url=api_schema_url,
        api_schema_type=api_schema_type,
        file=file,
    )

    if len(assets) == 0:
        console.error("No asset provided to the group command.")
        raise click.exceptions.Exit(2)

    logger.debug("scanning assets %s", [str(a) for a in assets])
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


def _build_links(
    link: tuple[str, ...], link_method: tuple[str, ...]
) -> list[asset_lib.Asset]:
    """Build Link assets, pairing each link with its method (defaults to GET)."""
    if len(link_method) > 0 and len(link_method) != len(link):
        console.error("Make sure every --link has its corresponding --link-method.")
        raise click.exceptions.Exit(2)
    methods = link_method if len(link_method) > 0 else ("GET",) * len(link)
    return [
        link_asset.Link(url=url, method=method) for url, method in zip(link, methods)
    ]


def _build_repositories(
    repository_url: tuple[str, ...],
    repository_commit_hash: tuple[str, ...],
    repository_provider: tuple[str, ...],
) -> list[asset_lib.Asset]:
    """Build Repository assets from parallel url / commit-hash / provider lists."""
    if len(repository_commit_hash) not in (0, len(repository_url)):
        console.error("Each --repository-url must have a --repository-commit-hash.")
        raise click.exceptions.Exit(2)
    if len(repository_provider) not in (0, len(repository_url)):
        console.error("Each --repository-url must have a --repository-provider.")
        raise click.exceptions.Exit(2)

    repositories: list[asset_lib.Asset] = []
    for index, url in enumerate(repository_url):
        commit_hash = (
            repository_commit_hash[index] if len(repository_commit_hash) > 0 else ""
        )
        provider = (
            repository_provider[index].upper() if len(repository_provider) > 0 else ""
        )
        repositories.append(
            repository_asset.Repository(
                repository_url=url,
                commit_hash=commit_hash,
                provider=provider,
            )
        )
    return repositories


def _build_api_schemas(
    api_schema_endpoint: tuple[str, ...],
    api_schema_url: tuple[str, ...],
    api_schema_type: tuple[str, ...],
) -> list[asset_lib.Asset]:
    """Build ApiSchema assets from parallel endpoint / url / type lists."""
    if len(api_schema_url) not in (0, len(api_schema_endpoint)):
        console.error("Each --api-schema-endpoint must have a --api-schema-url.")
        raise click.exceptions.Exit(2)
    if len(api_schema_type) not in (0, len(api_schema_endpoint)):
        console.error("Each --api-schema-endpoint must have a --api-schema-type.")
        raise click.exceptions.Exit(2)

    schemas: list[asset_lib.Asset] = []
    for index, endpoint in enumerate(api_schema_endpoint):
        content_url = api_schema_url[index] if len(api_schema_url) > 0 else None
        schema_type = api_schema_type[index] if len(api_schema_type) > 0 else None
        schemas.append(
            api_schema_asset.ApiSchema(
                endpoint_url=endpoint,
                content_url=content_url,
                schema_type=schema_type,
            )
        )
    return schemas


def _build_assets(
    apk: tuple[str, ...],
    ipa: tuple[str, ...],
    harmony_hap: tuple[str, ...],
    domain: tuple[str, ...],
    link: tuple[str, ...],
    link_method: tuple[str, ...],
    repository_url: tuple[str, ...],
    repository_commit_hash: tuple[str, ...],
    repository_provider: tuple[str, ...],
    api_schema_endpoint: tuple[str, ...],
    api_schema_url: tuple[str, ...],
    api_schema_type: tuple[str, ...],
    file: tuple[str, ...],
) -> list[asset_lib.Asset]:
    """Build the flat list of injectable assets from the group command options."""
    assets: list[asset_lib.Asset] = []
    assets.extend(android_apk_asset.AndroidApk(content_url=url) for url in apk)
    assets.extend(ios_ipa_asset.IOSIpa(content_url=url) for url in ipa)
    assets.extend(
        harmonyos_hap_asset.HarmonyOSHap(content_url=url) for url in harmony_hap
    )
    assets.extend(domain_name_asset.DomainName(name=name) for name in domain)
    assets.extend(_build_links(link, link_method))
    assets.extend(
        _build_repositories(repository_url, repository_commit_hash, repository_provider)
    )
    assets.extend(
        _build_api_schemas(api_schema_endpoint, api_schema_url, api_schema_type)
    )
    assets.extend(file_asset.File(content_url=url) for url in file)
    return assets
