"""Asset of type Risk.
This module takes care of preparing a risk message to be injected onto the message bus."""

import io
import ipaddress
import logging

import click

from ostorlab import exceptions
from ostorlab.assets import risk as risk_asset
from ostorlab.cli import console as cli_console
from ostorlab.cli.scan.run import run

logger = logging.getLogger(__name__)
console = cli_console.Console()

_RISK_RATINGS = [
    "CRITICAL",
    "HIGH",
    "MEDIUM",
    "LOW",
    "POTENTIALLY",
    "HARDENING",
    "SECURE",
    "IMPORTANT",
    "INFO",
]


@run.run.command(name="risk")
@click.option(
    "--severity",
    required=True,
    type=click.Choice(_RISK_RATINGS, case_sensitive=False),
    help="Risk severity.",
)
@click.option(
    "--description",
    required=False,
    default=None,
    help="Description of the risk.",
)
@click.option(
    "--description-file",
    type=click.File(mode="r"),
    required=False,
    default=None,
    help="Path to a file containing the risk description.",
)
@click.option(
    "--ip",
    "ip_addr",
    required=False,
    default=None,
    help="IP address the risk applies to.",
)
@click.option(
    "--domain",
    required=False,
    default=None,
    help="Domain name the risk applies to.",
)
@click.option(
    "--link",
    "url",
    required=False,
    default=None,
    help="URL the risk applies to.",
)
@click.option(
    "--link-method",
    default="GET",
    show_default=True,
    help="HTTP method for the link.",
)
@click.option(
    "--link-header",
    "link_headers",
    multiple=True,
    help="HTTP header in 'Name: Value' format. Can be repeated.",
)
@click.option(
    "--android-store",
    required=False,
    default=None,
    help="Android package name the risk applies to.",
)
@click.option(
    "--ios-store",
    required=False,
    default=None,
    help="iOS bundle ID the risk applies to.",
)
@click.option(
    "--android-aab",
    "android_aab_file",
    type=click.File(mode="rb"),
    required=False,
    default=None,
    help="Android AAB file the risk applies to.",
)
@click.option(
    "--android-aab-url",
    required=False,
    default=None,
    help="URL of the Android AAB the risk applies to.",
)
@click.option(
    "--android-apk",
    "android_apk_file",
    type=click.File(mode="rb"),
    required=False,
    default=None,
    help="Android APK file the risk applies to.",
)
@click.option(
    "--android-apk-url",
    required=False,
    default=None,
    help="URL of the Android APK the risk applies to.",
)
@click.option(
    "--ios-ipa",
    "ios_ipa_file",
    type=click.File(mode="rb"),
    required=False,
    default=None,
    help="iOS IPA file the risk applies to.",
)
@click.option(
    "--ios-ipa-url",
    required=False,
    default=None,
    help="URL of the iOS IPA the risk applies to.",
)
@click.option(
    "--api-schema-file",
    type=click.File(mode="rb"),
    required=False,
    default=None,
    help="API schema file the risk applies to.",
)
@click.option(
    "--api-schema-url",
    required=False,
    default=None,
    help="URL of the API schema the risk applies to.",
)
@click.option(
    "--api-schema-endpoint",
    required=False,
    default=None,
    help="API endpoint URL.",
)
@click.option(
    "--api-schema-type",
    required=False,
    default=None,
    help="API schema type (e.g. openapi, graphql, wsdl).",
)
@click.option(
    "--api-schema-header",
    "api_schema_headers",
    multiple=True,
    help="API schema HTTP header in 'Name: Value' format. Can be repeated.",
)
@click.option(
    "--repository-url",
    "--repository",
    required=False,
    default=None,
    help="Source code repository the risk applies to.",
)
@click.option(
    "--commit-hash",
    required=False,
    default=None,
    help="Commit hash for the source code repository.",
)
@click.option(
    "--repository-archive",
    "repository_archive_file",
    type=click.File(mode="rb"),
    required=False,
    default=None,
    help="Source code repository archive the risk applies to.",
)
@click.option(
    "--repository-archive-url",
    required=False,
    default=None,
    help="URL of the source code repository archive the risk applies to.",
)
@click.pass_context
def risk_cli(
    ctx: click.core.Context,
    severity: str,
    description: str | None,
    description_file: io.TextIOWrapper | None,
    ip_addr: str | None,
    domain: str | None,
    url: str | None,
    link_method: str,
    link_headers: tuple,
    android_store: str | None,
    ios_store: str | None,
    android_aab_file: io.RawIOBase | None,
    android_aab_url: str | None,
    android_apk_file: io.RawIOBase | None,
    android_apk_url: str | None,
    ios_ipa_file: io.RawIOBase | None,
    ios_ipa_url: str | None,
    api_schema_file: io.RawIOBase | None,
    api_schema_url: str | None,
    api_schema_endpoint: str | None,
    api_schema_type: str | None,
    api_schema_headers: tuple,
    repository_url: str | None,
    commit_hash: str | None,
    repository_archive_file: io.RawIOBase | None,
    repository_archive_url: str | None,
) -> None:
    """Run scan with a risk report injected onto the message bus.\n
    Example:\n
        - oxo scan run --agent=agent/ostorlab/nmap risk --severity HIGH --description "Server exposed" --ip 8.8.8.8\n
        - oxo scan run --agent=agent/ostorlab/nmap risk --severity HIGH --description-file report.txt --ip 8.8.8.8\n
        - oxo scan run --agent=agent/ostorlab/nmap risk --severity HIGH --description "Hardcoded secret" --repository-url https://github.com/org/repo --commit-hash abc123\n
        - oxo scan run --agent=agent/ostorlab/nmap risk --severity HIGH --description "Hardcoded secret" --repository-archive-url https://example.com/repo.zip
    """
    if description is None and description_file is None:
        console.error("Provide either --description or --description-file.")
        raise click.exceptions.Exit(2)
    if description is not None and description_file is not None:
        console.error("Provide either --description or --description-file, not both.")
        raise click.exceptions.Exit(2)
    if description_file is not None:
        description = description_file.read()

    if android_apk_file is not None and android_apk_url is not None:
        console.error("Provide either --android-apk or --android-apk-url, not both.")
        raise click.exceptions.Exit(2)
    if android_aab_file is not None and android_aab_url is not None:
        console.error("Provide either --android-aab or --android-aab-url, not both.")
        raise click.exceptions.Exit(2)
    if ios_ipa_file is not None and ios_ipa_url is not None:
        console.error("Provide either --ios-ipa or --ios-ipa-url, not both.")
        raise click.exceptions.Exit(2)
    if api_schema_file is not None and api_schema_url is not None:
        console.error("Provide either --api-schema-file or --api-schema-url, not both.")
        raise click.exceptions.Exit(2)
    if (repository_url is None) != (commit_hash is None):
        console.error("Provide both --repository-url and --commit-hash together.")
        raise click.exceptions.Exit(2)
    if repository_archive_file is not None and repository_archive_url is not None:
        console.error(
            "Provide either --repository-archive or --repository-archive-url, not both."
        )
        raise click.exceptions.Exit(2)

    runtime = ctx.obj["runtime"]

    risk_kwargs = {
        "description": description,
        "rating": severity,
    }

    if ip_addr is not None:
        try:
            ip_network = ipaddress.ip_network(ip_addr, strict=False)
        except ValueError:
            console.error(f"Invalid IP address: {ip_addr}")
            raise click.exceptions.Exit(2)
        if ip_network.version == 4:
            risk_kwargs["ipv4"] = {
                "host": ip_network.network_address.exploded,
                "mask": str(ip_network.prefixlen),
                "version": 4,
            }
        elif ip_network.version == 6:
            risk_kwargs["ipv6"] = {
                "host": ip_network.network_address.exploded,
                "mask": str(ip_network.prefixlen),
                "version": 6,
            }

    if domain is not None:
        risk_kwargs["domain_name"] = {"name": domain}

    if url is not None:
        link_dict: dict = {"url": url, "method": link_method}
        if len(link_headers) > 0:
            parsed_headers = []
            for h in link_headers:
                if ": " not in h:
                    console.error(
                        f"Invalid header format '{h}', expected 'Name: Value'."
                    )
                    raise click.exceptions.Exit(2)
                name, value = h.split(": ", 1)
                parsed_headers.append({"name": name, "value": value})
            link_dict["extra_headers"] = parsed_headers
        risk_kwargs["link"] = link_dict

    if android_store is not None:
        risk_kwargs["android_store"] = {"package_name": android_store}

    if ios_store is not None:
        risk_kwargs["ios_store"] = {"bundle_id": ios_store}

    if android_aab_file is not None:
        risk_kwargs["android_aab"] = {
            "content": android_aab_file.read(),
            "path": android_aab_file.name,
        }
    elif android_aab_url is not None:
        risk_kwargs["android_aab"] = {"content_url": android_aab_url}

    if android_apk_file is not None:
        risk_kwargs["android_apk"] = {
            "content": android_apk_file.read(),
            "path": android_apk_file.name,
        }
    elif android_apk_url is not None:
        risk_kwargs["android_apk"] = {"content_url": android_apk_url}

    if ios_ipa_file is not None:
        risk_kwargs["ios_ipa"] = {
            "content": ios_ipa_file.read(),
            "path": ios_ipa_file.name,
        }
    elif ios_ipa_url is not None:
        risk_kwargs["ios_ipa"] = {"content_url": ios_ipa_url}

    if (
        api_schema_file is not None
        or api_schema_url is not None
        or api_schema_endpoint is not None
    ):
        schema_dict: dict = {}
        if api_schema_file is not None:
            schema_dict["content"] = api_schema_file.read()
            schema_dict["path"] = api_schema_file.name
        if api_schema_url is not None:
            schema_dict["content_url"] = api_schema_url
        if api_schema_endpoint is not None:
            schema_dict["endpoint_url"] = api_schema_endpoint
        if api_schema_type is not None:
            schema_dict["schema_type"] = api_schema_type
        if len(api_schema_headers) > 0:
            parsed_schema_headers = []
            for h in api_schema_headers:
                if ": " not in h:
                    console.error(
                        f"Invalid header format '{h}', expected 'Name: Value'."
                    )
                    raise click.exceptions.Exit(2)
                name, value = h.split(": ", 1)
                parsed_schema_headers.append({"name": name, "value": value})
            schema_dict["extra_headers"] = parsed_schema_headers
        risk_kwargs["api_schema"] = schema_dict

    if repository_url is not None and commit_hash is not None:
        risk_kwargs["repository"] = {
            "repository_url": repository_url,
            "commit_hash": commit_hash,
        }

    if repository_archive_file is not None:
        risk_kwargs["repository_archive"] = {
            "content": repository_archive_file.read(),
            "path": repository_archive_file.name,
        }
    elif repository_archive_url is not None:
        risk_kwargs["repository_archive"] = {"content_url": repository_archive_url}

    assets = [risk_asset.Risk(**risk_kwargs)]

    logger.debug("injecting risk asset %s", assets)
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
