"""Unit tests for the import_scan module."""

from ostorlab.runtimes.local.app import utils
from ostorlab.runtimes.local.models import models
from ostorlab.utils import risk_rating


def testImportScan_always_shouldImportScan(
    zip_file_bytes: bytes,
) -> None:
    """Test import_scan function when the scan does not exist."""
    with models.Database() as session:
        assert session.query(models.Scan).count() == 0
        assert session.query(models.Vulnerability).count() == 0

        utils.import_scan_from_bytes(session, zip_file_bytes)

        assert session.query(models.Scan).count() == 1
        scan = session.query(models.Scan).first()
        assert scan.title == "swiftvulnerableapp-v0.7.ipa"
        assert scan.asset == "ios file"
        assert scan.progress == models.ScanProgress.DONE
        vulnerabilities = (
            session.query(models.Vulnerability)
            .filter(models.Vulnerability.scan_id == scan.id)
            .all()
        )
        assert len(vulnerabilities) == 423
        assert any(
            vuln.title == "Cryptographic Vulnerability: Insecure Algorithm"
            and vuln.risk_rating == risk_rating.RiskRating.MEDIUM
            for vuln in vulnerabilities
        )
