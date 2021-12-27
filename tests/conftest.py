"""Definitions of the fixtures that will be shared among multiple tests."""

import io
import pytest

from click import testing
import docker
import ruamel.yaml

from ostorlab.cli import rootcli


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
    json_schema_file_object =  io.StringIO(json_schema)
    return  json_schema_file_object


@pytest.fixture
def docker_dummy_image_cleanup():
    """Pytest fixture for removing all dummy images.
    """
    client = docker.from_env()
    yield client
    for img in client.images.list():
        _ = [client.images.remove(t) for t in img.tags if "dummy" in t]
