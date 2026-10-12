"""export utils module: contains utility functions to export the scan details."""

import datetime
import io
import ipaddress
import json
import logging
import pathlib
import zipfile
from typing import Any
from typing import Optional
from typing import cast

from ostorlab.runtimes.local.models import models

logger = logging.getLogger(__name__)

SCAN_JSON = "scan.json"
ASSET_JSON = "asset.json"
VULNERABILITY_JSON = "vulnerability.json"

RISK_RATINGS_ORDER = {
    "CRITICAL": 8,
    "HIGH": 7,
    "MEDIUM": 6,
    "LOW": 5,
    "POTENTIALLY": 4,
    "HARDENING": 3,
    "SECURE": 2,
    "IMPORTANT": 1,
    "INFO": 0,
}


def export_scan(scan: models.Scan, export_ide: Optional[bool] = False) -> bytes:
    """Export the scan details from the given file data.

    Args:
        scan: The scan object.
        export_ide: Whether to export the IDE or not.
    """
    fd = io.BytesIO()
    archive = zipfile.ZipFile(fd, "a", zipfile.ZIP_DEFLATED, True)

    _export_asset(scan.id, archive)
    _export_scan(scan, archive)
    _export_vulnz(scan.id, archive)

    if export_ide is True:
        pass

    archive.close()
    fd.seek(0)
    return fd.read()


def _export_asset(scan_id: int, archive: zipfile.ZipFile) -> None:
    """Export the asset details to the given archive.

    Args:
        scan_id: The scan id.
        archive: The archive object.
    """

    with models.Database() as session:
        assets = (
            session.query(models.Asset).filter(models.Asset.scan_id == scan_id).all()
        )
        if len(assets) == 0:
            return
        assets_data = []
        for asset in assets:
            asset_type = asset.type.replace("_", " ").lower()
            asset_dict = {
                "tags": None,
                "type": asset_type,
            }
            if asset.type == "android_file" or asset.type == "ios_file":
                path = _write_mobile_app(
                    cast(models.AndroidFile | models.IosFile, asset),
                    archive,
                    asset_type,
                )
                if path is not None:
                    asset_dict["path"] = path

            elif asset.type == "android_store":
                asset_dict["package_name"] = asset.package_name
                asset_dict["application_name"] = asset.application_name
            elif asset.type == "ios_store":
                asset_dict["package_name"] = asset.bundle_id
                asset_dict["application_name"] = asset.application_name
            elif asset.type == "network":
                networks = _get_network(asset)
                asset_dict["networks"] = networks
            elif asset.type == "urls":
                urls = _get_urls(asset)
                asset_dict["urls"] = urls
            else:
                raise NotImplementedError(f"Asset type {asset.type} not implemented.")

            assets_data.append(asset_dict)

        serialized_assets = "\n".join([json.dumps(asset) for asset in assets_data])
        archive.writestr(ASSET_JSON, serialized_assets)


def _write_mobile_app(
    asset: models.AndroidFile | models.IosFile,
    archive: zipfile.ZipFile,
    asset_type: str,
) -> str | None:
    """Write the mobile app to the given archive.

    Args:
        asset: The asset object.
        archive: The archive object.
        asset_type: The asset type.

    Returns:
        The mobile app name.
    """

    if asset.path is None:
        return None

    mobile_app = pathlib.Path(asset.path).name
    file_asset_path = pathlib.Path(asset.path)
    if file_asset_path.exists() is False:
        raise ValueError(f"{asset_type.capitalize()} File {asset.path} not found.")
    try:
        archive.writestr(mobile_app, file_asset_path.read_bytes())
        return mobile_app
    except Exception:
        logger.exception("Failed to write %s to archive", mobile_app)

    return None


def _get_network(asset: models.Asset) -> list[str]:
    """Get the network details from the given asset.

    Args:
        asset: The asset object.

    Returns:
        The network details.
    """
    with models.Database() as session:
        networks = []
        ips = (
            session.query(models.IPRange)
            .filter(models.IPRange.network_asset_id == asset.id)
            .all()
        )
        for ip in ips:
            ip_network = ipaddress.ip_network(ip.host, strict=False)
            networks.append(
                f"{ip_network.network_address.exploded}/{ip_network.prefixlen}"
            )
        return networks


def _get_urls(asset: models.Asset) -> list[str]:
    """Get the urls from the given asset.

    Args:
        asset: The asset object.

    Returns:
        The urls.
    """
    with models.Database() as session:
        urls = []
        links = (
            session.query(models.Link)
            .filter(models.Link.urls_asset_id == asset.id)
            .all()
        )
        for link in links:
            urls.append(link.url)

        return urls


def _export_scan(scan: models.Scan, archive: zipfile.ZipFile) -> None:
    """Export the scan details to the given archive.

    Args:
        scan: The scan object.
        archive: The archive object.
    """

    scan_dict: dict[str, Any] = {
        "title": scan.title,
        "created_time": cast(datetime.datetime, scan.created_time).strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "risk_rating": scan.risk_rating.name.lower()
        if scan.risk_rating is not None
        else None,
        "status": [],
    }

    with models.Database() as session:
        scan_statuses = (
            session.query(models.ScanStatus)
            .filter(models.ScanStatus.scan_id == scan.id)
            .all()
        )
        if len(scan_statuses) == 0:
            scan_statuses = [
                models.ScanStatus.create(
                    key="progress",
                    value=cast(models.ScanProgress, scan.progress).name.lower(),
                    scan_id=scan.id,
                )
            ]
        for status in scan_statuses:
            scan_dict["status"].append(
                {
                    "id": status.id,
                    "key": status.key,
                    "value": status.value,
                }
            )
        archive.writestr(SCAN_JSON, json.dumps(scan_dict))


def _export_vulnz(scan_id: int, archive: zipfile.ZipFile) -> None:
    """Export the vulnerabilities details to the given archive.

    Args:
        scan_id: The scan id.
        archive: The archive object.
    """

    with models.Database() as session:
        vulns_list = []
        vulnerabilities = session.query(models.Vulnerability).filter(
            models.Vulnerability.scan_id == scan_id
        )
        for vuln in vulnerabilities:
            references = (
                session.query(models.Reference)
                .filter(models.Reference.vulnerability_id == vuln.id)
                .all()
            )
            refs_list = [{"title": ref.title, "url": ref.url} for ref in references]
            kb_dict = {
                "title": vuln.title,
                "short_description": vuln.short_description,
                "description": vuln.description,
                "recommendation": vuln.recommendation,
                "risk_rating": vuln.risk_rating.name.lower(),
                "references": refs_list,
            }

            vulns_list.append(
                {
                    "detail": kb_dict,
                    "technical_detail": vuln.technical_detail,
                    "risk_rating": vuln.risk_rating.name.lower(),
                    "cvss_v3_vector": vuln.cvss_v3_vector,
                }
            )
        archive.writestr(VULNERABILITY_JSON, json.dumps(vulns_list))
