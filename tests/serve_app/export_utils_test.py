"""Unit tests for the export_utils module."""

import io
import json
import zipfile

from pytest_mock import plugin

from ostorlab.serve_app import export_utils, import_utils
from ostorlab.runtimes.local.models import models
from ostorlab.utils import risk_rating


def testExportScan_whenNetworkScan_shouldExportScan(
    network_scan: models.Scan,
    db_engine_path: str,
    mocker: plugin.MockerFixture,
    clean_db: None,
) -> None:
    """Test exporting a network scan."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)

    exported_bytes = export_utils.export_scan(scan=network_scan)

    fd = io.BytesIO(exported_bytes)
    with models.Database() as session:
        import_utils.import_scan(append_to_scan=network_scan, file_data=fd.read())
        scan = session.query(models.Scan).first()
        assert scan.title == "Network Scan"
        assert scan.progress == models.ScanProgress.IN_PROGRESS
        assert scan.risk_rating == risk_rating.RiskRating.HIGH
        vulnerabilities = (
            session.query(models.Vulnerability)
            .filter(models.Vulnerability.scan_id == scan.id)
            .all()
        )
        assert len(vulnerabilities) == 2
        assert any(
            vuln.title == "XSS" and vuln.risk_rating == risk_rating.RiskRating.HIGH
            for vuln in vulnerabilities
        )
        assert network_scan.progress == models.ScanProgress.IN_PROGRESS
        assets = (
            session.query(models.Asset).filter(models.Asset.scan_id == scan.id).all()
        )
        assert len(assets) == 2
        assert all(asset.type == "network" for asset in assets)


def testExportScan_whenWebScan_shouldExportScan(
    web_scan: models.Scan,
    db_engine_path: str,
    mocker: plugin.MockerFixture,
    clean_db: None,
) -> None:
    """Test exporting a web scan."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)

    exported_bytes = export_utils.export_scan(scan=web_scan)

    fd = io.BytesIO(exported_bytes)
    with models.Database() as session:
        import_utils.import_scan(append_to_scan=web_scan, file_data=fd.read())
        scan = session.query(models.Scan).first()
        assert scan.title == "Web Scan"
        assert scan.progress == models.ScanProgress.DONE
        assert scan.risk_rating == risk_rating.RiskRating.HIGH
        vulnerabilities = (
            session.query(models.Vulnerability)
            .filter(models.Vulnerability.scan_id == scan.id)
            .all()
        )
        assert len(vulnerabilities) == 2
        assert any(
            vuln.title == "XSS" and vuln.risk_rating == risk_rating.RiskRating.HIGH
            for vuln in vulnerabilities
        )
        assert web_scan.progress == models.ScanProgress.DONE
        assets = (
            session.query(models.Asset).filter(models.Asset.scan_id == scan.id).all()
        )
        assert len(assets) == 2
        assert all(asset.type == "urls" for asset in assets)


def testExportScan_whenAndroidFileScan_shouldExportScan(
    android_file_scan: models.Scan,
    db_engine_path: str,
    mocker: plugin.MockerFixture,
    clean_db: None,
) -> None:
    """Test exporting an Android file scan."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)

    exported_bytes = export_utils.export_scan(scan=android_file_scan)

    fd = io.BytesIO(exported_bytes)
    with models.Database() as session:
        import_utils.import_scan(append_to_scan=android_file_scan, file_data=fd.read())
        scan = session.query(models.Scan).first()
        assert scan.title == "Android File Scan"
        assert scan.progress == models.ScanProgress.IN_PROGRESS
        assert scan.risk_rating == risk_rating.RiskRating.MEDIUM
        vulnerabilities = (
            session.query(models.Vulnerability)
            .filter(models.Vulnerability.scan_id == scan.id)
            .all()
        )
        assert len(vulnerabilities) == 2
        assert any(
            vuln.title == "Insecure File Provider Paths Setting"
            and vuln.risk_rating == risk_rating.RiskRating.MEDIUM
            for vuln in vulnerabilities
        )
        assert android_file_scan.progress == models.ScanProgress.IN_PROGRESS
        assets = (
            session.query(models.Asset).filter(models.Asset.scan_id == scan.id).all()
        )
        assert len(assets) == 2
        assert all(asset.type == "android_file" for asset in assets)


def testExportScan_whenIOSFileScan_shouldExportScan(
    ios_file_scan: models.Scan,
    db_engine_path: str,
    mocker: plugin.MockerFixture,
    clean_db: None,
) -> None:
    """Test exporting an iOS file scan."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)

    exported_bytes = export_utils.export_scan(scan=ios_file_scan)

    fd = io.BytesIO(exported_bytes)
    with models.Database() as session:
        import_utils.import_scan(append_to_scan=ios_file_scan, file_data=fd.read())
        scan = session.query(models.Scan).first()
        assert scan.title == "IOS File Scan"
        assert scan.progress == models.ScanProgress.IN_PROGRESS
        assert scan.risk_rating == risk_rating.RiskRating.MEDIUM
        vulnerabilities = (
            session.query(models.Vulnerability)
            .filter(models.Vulnerability.scan_id == scan.id)
            .all()
        )
        assert len(vulnerabilities) == 2
        assert any(
            vuln.title == "Insecure App Transport Security (ATS) Settings"
            and vuln.risk_rating == risk_rating.RiskRating.MEDIUM
            for vuln in vulnerabilities
        )
        assert ios_file_scan.progress == models.ScanProgress.IN_PROGRESS
        assets = (
            session.query(models.Asset).filter(models.Asset.scan_id == scan.id).all()
        )
        assert len(assets) == 2
        assert all(asset.type == "ios_file" for asset in assets)


def testExportScan_whenAndroidStoreScan_shouldExportScan(
    android_store_scan: models.Scan,
    db_engine_path: str,
    mocker: plugin.MockerFixture,
    clean_db: None,
) -> None:
    """Test exporting an Android store scan."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)

    exported_bytes = export_utils.export_scan(scan=android_store_scan)

    fd = io.BytesIO(exported_bytes)
    with models.Database() as session:
        import_utils.import_scan(append_to_scan=android_store_scan, file_data=fd.read())
        scan = session.query(models.Scan).first()
        assert scan.title == "Android Store Scan"
        assert scan.progress == models.ScanProgress.IN_PROGRESS
        assert scan.risk_rating == risk_rating.RiskRating.MEDIUM
        vulnerabilities = (
            session.query(models.Vulnerability)
            .filter(models.Vulnerability.scan_id == scan.id)
            .all()
        )
        assert len(vulnerabilities) == 2
        assert any(
            vuln.title == "Insecure File Provider Paths Setting"
            and vuln.risk_rating == risk_rating.RiskRating.MEDIUM
            for vuln in vulnerabilities
        )
        assert android_store_scan.progress == models.ScanProgress.IN_PROGRESS
        assets = (
            session.query(models.Asset).filter(models.Asset.scan_id == scan.id).all()
        )
        assert len(assets) == 2
        assert all(asset.type == "android_store" for asset in assets)


def testExportScan_whenIOSStoreScan_shouldExportScan(
    ios_store_scan: models.Scan,
    db_engine_path: str,
    mocker: plugin.MockerFixture,
    clean_db: None,
) -> None:
    """Test exporting an iOS scan."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)

    exported_bytes = export_utils.export_scan(scan=ios_store_scan)

    fd = io.BytesIO(exported_bytes)
    with models.Database() as session:
        import_utils.import_scan(append_to_scan=ios_store_scan, file_data=fd.read())
        scan = session.query(models.Scan).first()
        assert scan.title == "IOS Store Scan"
        assert scan.progress == models.ScanProgress.IN_PROGRESS
        assert scan.risk_rating == risk_rating.RiskRating.MEDIUM
        vulnerabilities = (
            session.query(models.Vulnerability)
            .filter(models.Vulnerability.scan_id == scan.id)
            .all()
        )
        assert len(vulnerabilities) == 2
        assert any(
            vuln.title == "Insecure App Transport Security (ATS) Settings"
            and vuln.risk_rating == risk_rating.RiskRating.MEDIUM
            for vuln in vulnerabilities
        )
        assert ios_store_scan.progress == models.ScanProgress.IN_PROGRESS
        assets = (
            session.query(models.Asset).filter(models.Asset.scan_id == scan.id).all()
        )
        assert len(assets) == 2
        assert all(asset.type == "ios_store" for asset in assets)


def testExportScan_whenMultipleAssets_shouldExportScan(
    multiple_assets_scan: models.Scan,
    db_engine_path: str,
    mocker: plugin.MockerFixture,
) -> None:
    """Test exporting a scan with multiple assets."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)

    exported_bytes = export_utils.export_scan(scan=multiple_assets_scan)

    fd = io.BytesIO(exported_bytes)
    with models.Database() as session:
        import_utils.import_scan(
            append_to_scan=multiple_assets_scan, file_data=fd.read()
        )
        scan = session.query(models.Scan).first()
        assert scan.title == "Multiple Assets Scan"
        assert scan.progress == models.ScanProgress.IN_PROGRESS
        assert scan.risk_rating == risk_rating.RiskRating.HIGH
        vulnerabilities = (
            session.query(models.Vulnerability)
            .filter(models.Vulnerability.scan_id == scan.id)
            .all()
        )
        assert len(vulnerabilities) == 0
        assets = (
            session.query(models.Asset).filter(models.Asset.scan_id == scan.id).all()
        )
        assert len(assets) == 4
        assert any(asset.type == "android_file" for asset in assets)
        assert any(asset.type == "network" for asset in assets)


def testExportScan_whenScanHasNoVulz_exportRiskRatingAsNone(
    scan: models.Scan,
    db_engine_path: str,
    mocker: plugin.MockerFixture,
) -> None:
    """Test exporting a scan with no vulnerabilities."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)

    exported_bytes = export_utils.export_scan(scan=scan)

    with zipfile.ZipFile(io.BytesIO(exported_bytes), "r") as zip_file:
        with zip_file.open("scan.json") as scan_file:
            scan_data = json.load(scan_file)
            assert scan_data["risk_rating"] is None
