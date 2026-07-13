"""Asset of type Risk.
This module takes care of preparing a risk message to be injected onto the message bus."""

import io
import ipaddress
import json
import logging
from typing import Any, Optional

import click

from ostorlab.assets import risk as risk_asset
from ostorlab.cli import console as cli_console
from ostorlab.cli.scan.run import run
from ostorlab import exceptions

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


def _parse_headers(headers: list[str]) -> list[dict[str, str]]:
    """Parse a list of 'Name: Value' header strings into name/value dicts."""
    parsed_headers = []
    for header in headers:
        if ": " not in header:
            console.error(f"Invalid header format '{header}', expected 'Name: Value'.")
            raise click.exceptions.Exit(2)
        name, value = header.split(": ", 1)
        parsed_headers.append({"name": name, "value": value})
    return parsed_headers


def _build_link(
    url: Optional[str], method: str, headers: list[str]
) -> Optional[dict[str, Any]]:
    """Assemble a link sub-asset from a URL, HTTP method and headers."""
    if url is None:
        return None
    link_dict: dict[str, Any] = {"url": url, "method": method}
    if len(headers) > 0:
        link_dict["extra_headers"] = _parse_headers(headers)
    return link_dict


def _build_risk(
    severity: str,
    description: str,
    ip_addr: Optional[str] = None,
    domain: Optional[str] = None,
    link: Optional[dict[str, Any]] = None,
    android_store: Optional[str] = None,
    ios_store: Optional[str] = None,
    android_aab: Optional[dict[str, Any]] = None,
    android_apk: Optional[dict[str, Any]] = None,
    ios_ipa: Optional[dict[str, Any]] = None,
    api_schema: Optional[dict[str, Any]] = None,
    repository: Optional[dict[str, Any]] = None,
) -> risk_asset.Risk:
    """Build a Risk asset from already-resolved primitive fields and sub-assets."""
    risk_kwargs: dict[str, Any] = {
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
    if link is not None:
        risk_kwargs["link"] = link
    if android_store is not None:
        risk_kwargs["android_store"] = {"package_name": android_store}
    if ios_store is not None:
        risk_kwargs["ios_store"] = {"bundle_id": ios_store}
    if android_aab is not None:
        risk_kwargs["android_aab"] = android_aab
    if android_apk is not None:
        risk_kwargs["android_apk"] = android_apk
    if ios_ipa is not None:
        risk_kwargs["ios_ipa"] = ios_ipa
    if api_schema is not None:
        risk_kwargs["api_schema"] = api_schema
    if repository is not None:
        risk_kwargs["repository"] = repository

    return risk_asset.Risk(**risk_kwargs)


def _build_risk_from_mapping(entry: dict[str, Any]) -> risk_asset.Risk:
    """Build a Risk asset from a single JSON risk entry.

    File-backed assets (APK/AAB/IPA/API schema content) are only supported through
    their URL variants in JSON mode, since binary content cannot be embedded."""
    severity = entry.get("severity")
    if severity is None or severity.upper() not in _RISK_RATINGS:
        console.error(
            f"Each risk requires a valid 'severity', one of: {', '.join(_RISK_RATINGS)}."
        )
        raise click.exceptions.Exit(2)
    description = entry.get("description")
    if description is None:
        console.error("Each risk requires a 'description'.")
        raise click.exceptions.Exit(2)

    api_schema: Optional[dict[str, Any]] = None
    if (
        entry.get("api_schema_url") is not None
        or entry.get("api_schema_endpoint") is not None
    ):
        api_schema = {}
        if entry.get("api_schema_url") is not None:
            api_schema["content_url"] = entry["api_schema_url"]
        if entry.get("api_schema_endpoint") is not None:
            api_schema["endpoint_url"] = entry["api_schema_endpoint"]
        if entry.get("api_schema_type") is not None:
            api_schema["schema_type"] = entry["api_schema_type"]
        if entry.get("api_schema_headers") is not None:
            api_schema["extra_headers"] = _parse_headers(entry["api_schema_headers"])

    repository: Optional[dict[str, Any]] = None
    if entry.get("repository_url") is not None or entry.get("commit_hash") is not None:
        if entry.get("repository_url") is None or entry.get("commit_hash") is None:
            console.error("Provide both 'repository_url' and 'commit_hash' together.")
            raise click.exceptions.Exit(2)
        repository = {
            "repository_url": entry["repository_url"],
            "commit_hash": entry["commit_hash"],
        }

    def _content_url(key: str) -> Optional[dict[str, Any]]:
        value = entry.get(key)
        return {"content_url": value} if value is not None else None

    return _build_risk(
        severity=severity.upper(),
        description=description,
        ip_addr=entry.get("ip"),
        domain=entry.get("domain"),
        link=_build_link(
            entry.get("link"),
            entry.get("link_method", "GET"),
            entry.get("link_headers", []),
        ),
        android_store=entry.get("android_store"),
        ios_store=entry.get("ios_store"),
        android_aab=_content_url("android_aab_url"),
        android_apk=_content_url("android_apk_url"),
        ios_ipa=_content_url("ios_ipa_url"),
        api_schema=api_schema,
        repository=repository,
    )


@run.run.command(name="risk")
@click.option(
    "--severity",
    required=False,
    default=None,
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
    "--risks-file",
    type=click.File(mode="r"),
    required=False,
    default=None,
    help="Path to a JSON file with a list of risks to inject in a single scan.",
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
@click.pass_context
def risk_cli(
    ctx: click.core.Context,
    severity: Optional[str],
    description: Optional[str],
    description_file: Optional[io.TextIOWrapper],
    risks_file: Optional[io.TextIOWrapper],
    ip_addr: Optional[str],
    domain: Optional[str],
    url: Optional[str],
    link_method: str,
    link_headers: tuple[str, ...],
    android_store: Optional[str],
    ios_store: Optional[str],
    android_aab_file: Optional[io.RawIOBase],
    android_aab_url: Optional[str],
    android_apk_file: Optional[io.RawIOBase],
    android_apk_url: Optional[str],
    ios_ipa_file: Optional[io.RawIOBase],
    ios_ipa_url: Optional[str],
    api_schema_file: Optional[io.RawIOBase],
    api_schema_url: Optional[str],
    api_schema_endpoint: Optional[str],
    api_schema_type: Optional[str],
    api_schema_headers: tuple[str, ...],
    repository_url: Optional[str],
    commit_hash: Optional[str],
) -> None:
    """Run scan with one or more risk reports injected onto the message bus.\n
    Example:\n
        - oxo scan run --agent=agent/ostorlab/nmap risk --severity HIGH --description "Server exposed" --ip 8.8.8.8\n
        - oxo scan run --agent=agent/ostorlab/nmap risk --severity HIGH --description-file report.txt --ip 8.8.8.8\n
        - oxo scan run --agent=agent/ostorlab/nmap risk --risks-file risks.json
    """
    runtime = ctx.obj["runtime"]

    if risks_file is not None:
        if (
            severity is not None
            or description is not None
            or description_file is not None
        ):
            console.error(
                "Provide either --risks-file or the single-risk flags, not both."
            )
            raise click.exceptions.Exit(2)
        try:
            entries = json.loads(risks_file.read())
        except json.JSONDecodeError as e:
            console.error(f"Invalid JSON in risks file: {e}")
            raise click.exceptions.Exit(2)
        if isinstance(entries, list) is False or len(entries) == 0:
            console.error("Risks file must contain a non-empty JSON list of risks.")
            raise click.exceptions.Exit(2)
        assets = [_build_risk_from_mapping(entry) for entry in entries]
    else:
        if severity is None:
            console.error("Provide --severity or use --risks-file.")
            raise click.exceptions.Exit(2)
        if description is None and description_file is None:
            console.error("Provide either --description or --description-file.")
            raise click.exceptions.Exit(2)
        if description is not None and description_file is not None:
            console.error(
                "Provide either --description or --description-file, not both."
            )
            raise click.exceptions.Exit(2)
        if description_file is not None:
            description = description_file.read()
        assert description is not None

        if android_apk_file is not None and android_apk_url is not None:
            console.error(
                "Provide either --android-apk or --android-apk-url, not both."
            )
            raise click.exceptions.Exit(2)
        if android_aab_file is not None and android_aab_url is not None:
            console.error(
                "Provide either --android-aab or --android-aab-url, not both."
            )
            raise click.exceptions.Exit(2)
        if ios_ipa_file is not None and ios_ipa_url is not None:
            console.error("Provide either --ios-ipa or --ios-ipa-url, not both.")
            raise click.exceptions.Exit(2)
        if api_schema_file is not None and api_schema_url is not None:
            console.error(
                "Provide either --api-schema-file or --api-schema-url, not both."
            )
            raise click.exceptions.Exit(2)
        if (repository_url is None) != (commit_hash is None):
            console.error("Provide both --repository-url and --commit-hash together.")
            raise click.exceptions.Exit(2)

        android_aab: Optional[dict[str, Any]] = None
        if android_aab_file is not None:
            android_aab = {
                "content": android_aab_file.read(),
                "path": android_aab_file.name,
            }
        elif android_aab_url is not None:
            android_aab = {"content_url": android_aab_url}

        android_apk: Optional[dict[str, Any]] = None
        if android_apk_file is not None:
            android_apk = {
                "content": android_apk_file.read(),
                "path": android_apk_file.name,
            }
        elif android_apk_url is not None:
            android_apk = {"content_url": android_apk_url}

        ios_ipa: Optional[dict[str, Any]] = None
        if ios_ipa_file is not None:
            ios_ipa = {
                "content": ios_ipa_file.read(),
                "path": ios_ipa_file.name,
            }
        elif ios_ipa_url is not None:
            ios_ipa = {"content_url": ios_ipa_url}

        api_schema: Optional[dict[str, Any]] = None
        if (
            api_schema_file is not None
            or api_schema_url is not None
            or api_schema_endpoint is not None
        ):
            api_schema = {}
            if api_schema_file is not None:
                api_schema["content"] = api_schema_file.read()
                api_schema["path"] = api_schema_file.name
            if api_schema_url is not None:
                api_schema["content_url"] = api_schema_url
            if api_schema_endpoint is not None:
                api_schema["endpoint_url"] = api_schema_endpoint
            if api_schema_type is not None:
                api_schema["schema_type"] = api_schema_type
            if len(api_schema_headers) > 0:
                api_schema["extra_headers"] = _parse_headers(list(api_schema_headers))

        repository: Optional[dict[str, Any]] = None
        if repository_url is not None and commit_hash is not None:
            repository = {
                "repository_url": repository_url,
                "commit_hash": commit_hash,
            }

        assets = [
            _build_risk(
                severity=severity,
                description=description,
                ip_addr=ip_addr,
                domain=domain,
                link=_build_link(url, link_method, list(link_headers)),
                android_store=android_store,
                ios_store=ios_store,
                android_aab=android_aab,
                android_apk=android_apk,
                ios_ipa=ios_ipa,
                api_schema=api_schema,
                repository=repository,
            )
        ]

    logger.debug("injecting risk assets %s", assets)
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
