"""import utils module: contains utility functions to import the scan details."""

import datetime
import io
import ipaddress
import json
import uuid
import zipfile
from typing import Optional

from ostorlab import configuration_manager
from ostorlab.runtimes.local.models import models
from ostorlab.serve_app import common

SCAN_JSON = "scan.json"
ASSET_JSON = "asset.json"
VULNERABILITY_JSON = "vulnerability.json"
MOBILE_APP = "mobile.app"


def import_scan(
    file_data: bytes,
    append_to_scan: Optional[models.Scan] = None,
) -> None:
    """Import the scan details from the given file data.

    Args:
        file_data (bytes): The file data to import.
        append_to_scan (Optional[models.Scan], optional): The scan to append to. Defaults to None.
    """
    file = io.BytesIO(file_data)
    scan = append_to_scan or models.Scan()
    with zipfile.ZipFile(file, "r", zipfile.ZIP_DEFLATED, True) as archive:
        _import_scan(scan, archive)
        _import_vulnz(scan, archive)


def _import_scan(scan: models.Scan, archive: zipfile.ZipFile) -> None:
    with models.Database() as session:
        scan_dict = json.loads(archive.read(SCAN_JSON))
        asset_dict = json.loads(archive.read(ASSET_JSON))
        scan.title = scan_dict.get("title")
        scan.asset = asset_dict.get("type")
        scan.created_time = (
            datetime.datetime.strptime(
                scan_dict.get("created_time"), "%Y-%m-%d %H:%M:%S"
            )
            if scan_dict.get("created_time") is not None
            else datetime.datetime.now()
        )
        last_status: Optional[str] = None

        if scan.id is None:
            session.add(scan)
        session.commit()

        for status in sorted(scan_dict["status"], key=lambda s: s["id"]):
            scan_id: int = scan.id
            models.ScanStatus.create(
                key=status["key"], value=status["value"], scan_id=scan_id
            )
            if status["key"] == "progress":
                last_status = status["value"].upper()
        scan.progress = models.ScanProgress[last_status]
        session.commit()

        _import_asset(scan.id, archive)


def _import_vulnz(scan: models.Scan, archive: zipfile.ZipFile) -> None:
    vulnerabilities = json.loads(archive.read(VULNERABILITY_JSON))
    for vulnerability in vulnerabilities:
        models.Vulnerability.create(
            technical_detail=vulnerability.get("technical_detail"),
            risk_rating=vulnerability.get("risk_rating").upper(),
            title=vulnerability.get("detail").get("title"),
            short_description=vulnerability.get("detail").get("short_description"),
            description=vulnerability.get("detail").get("description"),
            recommendation=vulnerability.get("detail").get("recommendation"),
            scan_id=scan.id,
            references=vulnerability.get("detail").get("references"),
            location=vulnerability.get("detail").get("location"),
            cvss_v3_vector=vulnerability.get("cvss_v3_vector"),
        )


def _import_asset(scan_id: int, archive: zipfile.ZipFile) -> None:
    if ASSET_JSON not in archive.namelist():
        return None
    asset_dict = json.loads(archive.read(ASSET_JSON))
    config_manager = configuration_manager.ConfigurationManager()

    if "android file" in asset_dict["type"].lower():
        if MOBILE_APP in archive.namelist():
            content = archive.read(MOBILE_APP)
            android_file_path = (
                config_manager.upload_path / f"android_{str(uuid.uuid4())}"
            )
            android_file_path.write_bytes(content)
            models.AndroidFile.create(
                package_name=common.get_package_name(str(android_file_path)),
                path=str(android_file_path),
                scan_id=scan_id,
            )

    elif "ios file" in asset_dict["type"].lower():
        if MOBILE_APP in archive.namelist():
            content = archive.read(MOBILE_APP)
            ios_file_path = config_manager.upload_path / f"ios_{str(uuid.uuid4())}"
            ios_file_path.write_bytes(content)
            models.IosFile.create(
                bundle_id=common.get_bundle_id(str(ios_file_path)),
                path=str(ios_file_path),
                scan_id=scan_id,
            )

    elif "url" in asset_dict["type"].lower():
        urls = []
        for url in asset_dict["urls"]:
            urls.append({"url": url, "method": "GET"})
        models.Urls.create(
            links=urls,
            scan_id=scan_id,
        )

    elif "networks" in asset_dict["type"].lower():
        networks = []
        for network in asset_dict["networks"]:
            ip_network = ipaddress.ip_network(network, strict=False)
            networks.append(
                {
                    "host": ip_network.network_address.exploded,
                    "mask": str(ip_network.prefixlen),
                }
            )
        models.Network.create(
            networks=networks,
            scan_id=scan_id,
        )

    elif "android store" in asset_dict["type"].lower():
        application_name = asset_dict["application_name"]
        package_name = asset_dict["package_name"]
        models.AndroidStore.create(
            application_name=application_name,
            package_name=package_name,
            scan_id=scan_id,
        )

    elif "ios store" in asset_dict["type"].lower():
        application_name = asset_dict["application_name"]
        bundle_id = asset_dict["package_name"]
        models.IosStore.create(
            application_name=application_name,
            bundle_id=bundle_id,
            scan_id=scan_id,
        )

    else:
        raise NotImplementedError()
