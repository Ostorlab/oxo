"""Definitions of the fixtures that will be shared among multiple tests."""

import io
import time

import pytest
import docker

from ostorlab.runtimes.local.services import mq
from docker.models import services as services_model


@pytest.fixture(scope='session')
def mq_service():
    """Start MQ Docker service"""
    lrm = mq.LocalRabbitMQ(name='core_mq', network='test_network',
                           exposed_ports={5672: 5672})
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
                    "enum": ["run_once", "always_restart"]
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
def docker_dummy_image_cleanup():
    """Pytest fixture for removing all dummy images."""
    client = docker.from_env()
    yield client
    for img in client.images.list():
        for t in img.tags:
            if 'dummy' in t:
                client.images.remove(t)


# def docker_services():
#     """Pytest fixture for."""
#     service = {'ID': '0099i5n1y3gycuekvksyqyxav',
#                'Version': {'Index': 2338134},
#                'CreatedAt': '2021-12-27T13:37:02.795789947Z',
#                'UpdatedAt': '2022-01-07T15:06:19.777037132Z',
#                'Spec': {'Name': 'mq_qmwjef',
#                         'Labels': {'ostorlab.mq': '', 'ostorlab.universe': 'qmwjef'},
#                         'TaskTemplate': {'ContainerSpec': {'Image': 'rabbitmq:3.9-management',
#                                                            'Env': ['TASK_ID={{.Task.Slot}}',
#                                                                    'MQ_SERVICE_NAME=mq_qmwjef',
#                                                                    'RABBITMQ_ERLANG_COOKIE=2797cb34ff391e34567a'],
#                                                            'Isolation': 'default'},
#                                          'RestartPolicy': {'Condition': 'any',
#                                                            'Delay': 0,
#                                                            'MaxAttempts': 0,
#                                                            'Window': 0},
#                                          'Networks': [{'Target': '8z3orlqb21w8ka0n8vqfq940h'}],
#                                          'ForceUpdate': 0,
#                                          'Runtime': 'container'},
#                         'Mode': {'Replicated': {'Replicas': 1}},
#                         'EndpointSpec': {'Mode': 'vip'}},
#                'Endpoint': {'Spec': {'Mode': 'vip'},
#                             'VirtualIPs': [{'NetworkID': '8z3orlqb21w8ka0n8vqfq940h',
#                                             'Addr': '10.0.1.53/24'}]}}

#     return [services_model.Service(attrs=service)]
