"""import utils module: contains utility functions to import the scan details."""

import datetime
import io
import json
import zipfile
from typing import Optional

from ostorlab.runtimes.local.models import models

SCAN_JSON = "scan.json"
ASSET_JSON = "asset.json"
VULNERABILITY_JSON = "vulnerability.json"


def import_scan(
    session: models.Database,
    file_data: bytes,
    append_to_scan: Optional[models.Scan] = None,
) -> None:
    """Import the scan details from the given file data.

    Args:
        session (models.Database): The database session.
        file_data (bytes): The file data to import.
        append_to_scan (Optional[models.Scan], optional): The scan to append to. Defaults to None.
    """
    file = io.BytesIO(file_data)
    scan = append_to_scan or models.Scan()
    with zipfile.ZipFile(file, "r", zipfile.ZIP_DEFLATED, True) as archive:
        _import_scan(scan, archive, session)
        _import_vulnz(scan, archive)


def _import_scan(
    scan: models.Scan, archive: zipfile.ZipFile, session: models.Database
) -> None:
    scan_dict = json.loads(archive.read(SCAN_JSON))
    asset_dict = json.loads(archive.read(ASSET_JSON))
    scan.title = scan_dict.get("title")
    scan.asset = asset_dict.get("type")
    scan.created_time = (
        datetime.datetime.strptime(scan_dict.get("created_time"), "%Y-%m-%d %H:%M:%S")
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
