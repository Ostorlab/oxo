"""Tests for Models class."""
from ostorlab.runtimes.local import models
from unittest import mock


@mock.patch('ostorlab.runtimes.local.models.ENGINE_URL', 'sqlite:////tmp/ostorlab_db.sqlite')
def testModelsScan_whenDatabaseDoesNotExist_DatabaseAndScanCreated():
    """Test Agent implementation."""
    models.Database().create_db_tables()
    models.Scan.save('test')
    assert models.Database().session.query(models.Scan).count() == 1
    assert models.Database().session.query(models.Scan).all()[0].title == 'test'
    models.Database().drop_db_tables()


@mock.patch('ostorlab.runtimes.local.models.ENGINE_URL', 'sqlite:////tmp/ostorlab_db1.sqlite')
def testModelsVulnerability_whenDatabaseDoesNotExist_DatabaseAndScanCreated():
    """Test Agent implementation."""
    models.Database().create_db_tables()
    scan = models.Scan.save('test')
    models.Vulnerability.save(title='MyVuln', short_description= 'Xss', description= 'Javascript Vuln',
    recommendation= 'Sanitize data', technical_detail= 'a=$input', risk_rating= 'HIGH',
    cvss_v3_vector= '5:6:7', dna= '121312', false_positive=False, scan_id=scan.id)

    assert models.Database().session.query(models.Vulnerability).count() == 1
    assert models.Database().session.query(models.Vulnerability).all()[0].title == 'MyVuln'
    assert models.Database().session.query(models.Vulnerability).all()[0].scan_id == 1
    models.Database().drop_db_tables()


@mock.patch('ostorlab.runtimes.local.models.ENGINE_URL', 'sqlite:////tmp/ostorlab_db1.sqlite')
def testModelsScanStatus_whenDatabaseDoesNotExist_DatabaseAndScanCreated():
    """Test Agent implementation."""
    models.Database().create_db_tables()
    scan = models.Scan.save('test')
    models.ScanStatus.save(key='status', value= 'in_progress', scan_id=scan.id)

    assert models.Database().session.query(models.ScanStatus).count() == 1
    assert models.Database().session.query(models.ScanStatus).all()[0].key == 'status'
    assert models.Database().session.query(models.ScanStatus).all()[0].value == 'in_progress'
    assert models.Database().session.query(models.ScanStatus).all()[0].scan_id == 1
    models.Database().drop_db_tables()
