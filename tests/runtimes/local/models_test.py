"""Tests for Models class."""
from ostorlab.runtimes.local import models
from unittest import mock


@mock.patch('ostorlab.runtimes.local.models.ENGINE_URL', 'sqlite:////tmp/ostorlab_db.sqlite')
def testModelsScan_whenDatabaseDoesNotExist_DatabaseAndScanCreated(create_db_tables):
    """Test Scan Model implementation."""
    init_count = models.Database().session.query(models.Scan).count()
    models.Scan.save('test')

    assert models.Database().session.query(models.Scan).count() == init_count + 1
    assert models.Database().session.query(models.Scan).all()[-1].title == 'test'


@mock.patch('ostorlab.runtimes.local.models.ENGINE_URL', 'sqlite:////tmp/ostorlab_db1.sqlite')
def testModelsVulnerability_whenDatabaseDoesNotExist_DatabaseAndScanCreated(create_scan_db):
    """Test Vulnerability Model implementation."""
    init_count = models.Database().session.query(models.Vulnerability).count()
    models.Vulnerability.save(title='MyVuln', short_description= 'Xss', description= 'Javascript Vuln',
    recommendation= 'Sanitize data', technical_detail= 'a=$input', risk_rating= 'HIGH',
    cvss_v3_vector= '5:6:7', dna= '121312', false_positive=False, scan_id=create_scan_db.id)

    assert models.Database().session.query(models.Vulnerability).count() == init_count + 1
    assert models.Database().session.query(models.Vulnerability).all()[0].title == 'MyVuln'
    assert models.Database().session.query(models.Vulnerability).all()[0].scan_id == create_scan_db.id


@mock.patch('ostorlab.runtimes.local.models.ENGINE_URL', 'sqlite:////tmp/ostorlab_db1.sqlite')
def testModelsScanStatus_whenDatabaseDoesNotExist_DatabaseAndScanCreated(create_scan_db):
    """Test Scan Status Model implementation."""
    init_count = models.Database().session.query(models.ScanStatus).count()
    models.ScanStatus.save(key='status', value='in_progress', scan_id=create_scan_db.id)

    assert models.Database().session.query(models.ScanStatus).count() == init_count + 1
    assert models.Database().session.query(models.ScanStatus).all()[-1].key == 'status'
    assert models.Database().session.query(models.ScanStatus).all()[-1].value == 'in_progress'
    assert models.Database().session.query(models.ScanStatus).all()[-1].scan_id == create_scan_db.id

