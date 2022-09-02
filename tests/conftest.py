"""Definitions of the fixtures that will be shared among multiple tests."""

import io
import time
import sys

import pytest
import docker
import redis

from ostorlab.runtimes.local.services import mq
from ostorlab.runtimes.local.services import redis as local_redis_service


@pytest.fixture(scope='session')
def mq_service():
    """Start MQ Docker service"""
    lrm = mq.LocalRabbitMQ(name='core_mq', network='test_network', exposed_ports={5672: 5672, 15672: 15672})
    lrm.start()
    time.sleep(3)
    yield lrm
    lrm.stop()


@pytest.fixture(scope='session')
def redis_service():
    """Start Redis Docker service"""
    lr = local_redis_service.LocalRedis(name='core_redis', network='test_network', exposed_ports={6379: 6379})
    lr.start()
    time.sleep(3)
    yield lr
    lr.stop()


@pytest.fixture
def json_schema_file() -> io.StringIO:
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
                },
                "args": {
                    "description": "[Optional] - Array of dictionary-like objects, defining the agent arguments.",
                    "type": "array",
                    "items": {
                        "description": "Dictionary-like object of the argument.",
                        "type": "object",
                        "properties": {
                            "name": {
                                "description": "[Required] - Name of the agent argument.",
                                "type": "string",
                                "maxLength": 2048
                            },
                            "type": {
                                "description": "[Required] - Type of the agent argument : respecting the jsonschema types.",
                                "type": "string",
                                "maxLength": 2048
                            }
                        },
                        "required": ["name", "type"]
                    }
                }
            },
            "required": ["name", "image", "source", "durability", "restrictions", "in_selectors", "out_selectors", "restart_policy", "args"]
        }

    """
    json_schema_file_object = io.StringIO(json_schema)
    return json_schema_file_object


@pytest.fixture
def agent_group_json_schema_file() -> io.StringIO:
    """Agent group json schema is made a fixture since it will be used by multiple unit tests.

    Returns:
      json_schema_file_object : a file object of the agent group json schema file.

    """
    json_schema = """
        {
            "CustomTypes": {
                "agentArgument": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "maxLength": 2048
                        },
                        "type": {
                            "type": "string",
                            "maxLength": 2048
                        }
                    },
                    "required": ["name", "type"]
                }
            },
            "properties": {
                "description":{
                    "type": "string"
                },
                "kind":{
                    "type": "string",
                    "enum": [
                        "AgentGroup"
                    ]
                },
                "agents": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "key": {
                                "type": "string"
                            },
                            "args": {
                                "type": "array",
                                "items": {
                                    "$ref": "#/CustomTypes/agentArgument"
                                },
                                "default": []
                            }
                        },
                        "required": ["key", "args"]
                    }
                }
            },
            "required": ["kind", "description", "agents"]
        }

    """
    json_schema_file_object = io.StringIO(json_schema)
    return json_schema_file_object


@pytest.fixture()
def image_cleanup(request):
    """Pytest fixture for removing docker image with a specified tag."""
    client = docker.from_env()
    yield client
    tag = request.param
    for img in client.images.list():
        for t in img.tags:
            if tag in t:
                client.images.remove(t)


@pytest.fixture()
def db_engine_path(tmpdir):
    if sys.platform == 'win32':
        path = f'sqlite:///{tmpdir}\\ostorlab_db1.sqlite'.replace('\\', '\\\\')
    else:
        path = f'sqlite:////{tmpdir}/ostorlab_db1.sqlite'
    return path


@pytest.fixture()
def clean_redis_data(request) -> None:
    """Clean all redis data."""
    yield
    redis_url = request.param
    redis_client = redis.Redis.from_url(redis_url)
    keys = redis_client.keys()
    for key in keys:
        redis_client.delete(key)
