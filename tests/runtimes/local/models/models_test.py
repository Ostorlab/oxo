"""Tests for Models class."""
from ostorlab.runtimes.local.models import models
from unittest import mock


@mock.patch('ostorlab.runtimes.local.models.models.ENGINE_URL', 'sqlite:////tmp/ostorlab_db.sqlite')
def testModels_whenDatabaseDoesNotExist_DatabaseAndScanCreated():
    """Test when database does not exists, scan is populated in a newly created database."""
    models.Database().create_db_tables()
    models.Scan.create('test')
    assert models.Database().session.query(models.Scan).count() == 1
    assert models.Database().session.query(models.Scan).all()[0].title == 'test'
    models.Database().drop_db_tables()


@mock.patch('ostorlab.runtimes.local.models.models.ENGINE_URL', 'sqlite:////tmp/ostorlab_db2.sqlite')
def testScanUpdate_always_updatesExistingScan():
    """Test Agent save implementation."""
    models.Database().create_db_tables()
    models.Scan.create('test')

    database = models.Database()
    database.session.commit()
    assert database.session.query(models.Scan).count() == 1
    scan = database.session.query(models.Scan).first()
    scan.title = 'test2'
    database.session.commit()

    assert database.session.query(models.Scan).count() == 1
    scan = database.session.query(models.Scan).first()
    assert scan.title == 'test2'
