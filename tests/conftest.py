"""Definitions of the fixtures that will be shared among multiple tests."""

import io
import time

import pytest
import docker

from ostorlab.runtimes.local.services import mq
from ostorlab.runtimes.local.models import models

@pytest.fixture(scope='session')
def mq_service():
    """Start MQ Docker service"""
    lrm = mq.LocalRabbitMQ(name='core_mq', network='test_network', exposed_ports={5672: 5672})
    lrm.start()
    time.sleep(3)
    yield lrm
    lrm.stop()


@pytest.fixture
def json_schema_file():
    """Json schema is made a fixture since it will be used by multiple unit tests.

    Returns:
      json_schema_file_object : a file object of the json schema file.

    """
    json_schema = """
        {
            "CustomTypes": {
                "ArrayOfStrings": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "maxLength": 4096
                    }
                }
            },
            "properties": {
                "name": {
                    "type": "string",
                    "maxLength": 2048
                },
                "description":{
                    "type": "string"
                },
                "image":{
                    "type": "string",
                    "pattern": "((?:[^/]*/)*)(.*)"
                },
                "source":{
                    "type": "string",
                    "format": "uri",
                    "pattern": "^https?://",
                    "maxLength": 4096
                },
                "license":{
                    "type": "string",
                    "maxLength": 1024
                },
                "durability":{
                    "type": "string",
                    "enum": ["temporary", "development", "published"]
                },
                "restrictions": {
                    "$ref": "#/CustomTypes/ArrayOfStrings"
                },

                "in_selectors":{
                    "$ref": "#/CustomTypes/ArrayOfStrings"
                },

                "out_selectors":{
                    "$ref": "#/CustomTypes/ArrayOfStrings"
                },
                "restart_policy":{
                    "type": "string",
                    "enum": ["any", "on-failure", "none"]
                },
                "constraints":{
                    "$ref": "#/CustomTypes/ArrayOfStrings"
                },
                "mounts":{
                    "$ref": "#/CustomTypes/ArrayOfStrings"
                },
                "mem_limit":{
                    "type": "number"
                }
            },
            "required": ["name", "image", "source", "durability", "restrictions", "in_selectors", "out_selectors", "restart_policy"]
        }

    """
    json_schema_file_object = io.StringIO(json_schema)
    return json_schema_file_object


@pytest.fixture
def image_cleanup():
    """Pytest fixture for removing docker image with a specified tag."""
    def _image_cleanup(tag):
        client = docker.from_env()
        yield client
        for img in client.images.list():
            for t in img.tags:
                if tag in t:
                    client.images.remove(t)
    return _image_cleanup


@pytest.fixture
def vuln_db():
    """Pytest fixture for add a scan and a vulnerability."""
    models.Database().create_db_tables()
    create_scan_db = models.Scan.create('test')
    return models.Vulnerability.create(title='MyVuln', short_description= 'Xss', description= 'Javascript Vuln',
    recommendation= 'Sanitize data', technical_detail= 'a=$input', risk_rating= 'HIGH',
    cvss_v3_vector= '5:6:7', dna= '121312', scan_id=create_scan_db.id)
