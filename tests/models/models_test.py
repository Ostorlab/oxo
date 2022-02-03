"""Tests for Models class."""
from ostorlab.models import models
from unittest import mock


@mock.patch('ostorlab.models.models.ENGINE_URL', 'sqlite:////tmp/ostorlab_db.sqlite')
def testModels_whenDatabaseDoesNotExist_DatabaseAndScanCreated():
    """Test Agent implementation."""
    models.Database().create_db_tables()
    models.Scan.save('test')
    assert models.Database().session().query(models.Scan).count() == 1
    assert models.Database().session().query(models.Scan).all()[0].title == 'test'
    models.Database().drop_db_tables()
