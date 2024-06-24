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
        import_utils.import_scan(
            append_to_scan=network_scan, session=session, file_data=fd.read()
        )
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
        import_utils.import_scan(
            append_to_scan=web_scan, session=session, file_data=fd.read()
        )
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
        import_utils.import_scan(
            append_to_scan=android_file_scan, session=session, file_data=fd.read()
        )
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
        import_utils.import_scan(
            append_to_scan=ios_file_scan, session=session, file_data=fd.read()
        )
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
        import_utils.import_scan(
            append_to_scan=android_store_scan, session=session, file_data=fd.read()
        )
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
        import_utils.import_scan(
            append_to_scan=ios_store_scan, session=session, file_data=fd.read()
        )
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
