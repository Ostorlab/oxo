"""utils module: contains utility functions to export/import the scan details."""

import io
import json
import zipfile

from ostorlab.runtimes.local.models import models
from ostorlab.utils import risk_rating

SCAN_JSON = "scan.json"
ASSET_JSON = "asset.json"
VULNERABILITY_JSON = "vulnerability.json"


def import_scan_from_bytes(
    session: models.Database,
    file_data: bytes,
    append_to_scan: models.Scan | None = None,
) -> None:
    file = io.BytesIO(file_data)
    scan = append_to_scan or models.Scan()
    with zipfile.ZipFile(file, "r", zipfile.ZIP_DEFLATED, True) as archive:
        _import_scan(scan, archive, session)
        _import_vulnz(scan, archive, session)


def _import_scan(
    scan: models.Scan, archive: zipfile.ZipFile, session: models.Database
) -> None:
    scan_dict = json.loads(archive.read(SCAN_JSON))
    asset_dict = json.loads(archive.read(ASSET_JSON))
    scan.title = scan_dict.get("title")
    scan.asset = asset_dict.get("type")
    last_status: str | None = None
    for status in sorted(scan_dict["status"], key=lambda s: s["id"]):
        if status["key"] == "progress":
            models.ScanStatus.create(
                key=status["key"], value=status["value"], scan_id=scan.id
            )
            last_status = status["value"].upper()
    scan.progress = models.ScanProgress[last_status]

    if scan.id is None:
        session.add(scan)
    session.commit()


def _import_vulnz(
    scan: models.Scan, archive: zipfile.ZipFile, session: models.Database
) -> None:
    vulnerabilities = json.loads(archive.read(VULNERABILITY_JSON))
    for vulnerability in vulnerabilities:
        vulnz = models.Vulnerability(
            technical_detail=vulnerability["technical_detail"],
            risk_rating=risk_rating.RiskRating[
                vulnerability["custom_risk_rating"].upper()
            ],
            title=vulnerability["detail"]["title"],
            short_description=vulnerability["detail"]["short_description"],
            description=vulnerability["detail"]["description"],
            recommendation=vulnerability["detail"]["recommendation"],
            scan_id=scan.id,
        )
        session.add(vulnz)
    session.commit()
