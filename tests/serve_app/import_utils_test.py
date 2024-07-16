"""Unit tests for the import_scan module."""

from ostorlab.serve_app import import_utils
from ostorlab.runtimes.local.models import models
from ostorlab.utils import risk_rating


def testImportScan_always_shouldImportScan(
    zip_file_bytes: bytes,
) -> None:
    """Test import_scan function when the scan does not exist."""
    with models.Database() as session:
        import_utils.import_scan(zip_file_bytes)

        scan = session.query(models.Scan).all()[-1]
        assert scan.title == "swiftvulnerableapp-v0.7.ipa"
        assert scan.progress == models.ScanProgress.DONE
        assert scan.risk_rating == risk_rating.RiskRating.HIGH
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
