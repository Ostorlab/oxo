"""Unit tests for the export_utils module."""

import io

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
        assert scan.asset == "Network"
        assert scan.progress == models.ScanProgress.IN_PROGRESS
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
        assert scan.asset == "Web"
        assert scan.progress == models.ScanProgress.DONE
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
        assert scan.asset == "Android file"
        assert scan.progress == models.ScanProgress.IN_PROGRESS
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
        assert scan.asset == "IOS file"
        assert scan.progress == models.ScanProgress.IN_PROGRESS
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
        assert scan.asset == "Android store"
        assert scan.progress == models.ScanProgress.IN_PROGRESS
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
        assert scan.asset == "IOS store"
        assert scan.progress == models.ScanProgress.IN_PROGRESS
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
        assert scan.asset == "Android File, Network(s): 8.8.8.8/32, 8.8.4.4/32"
        assert scan.progress == models.ScanProgress.IN_PROGRESS
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
