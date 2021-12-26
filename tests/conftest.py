"""Definitions of the fixtures that will be shared among multiple tests.
"""

from io import StringIO
import pytest

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
    json_schema_file_object =  StringIO(json_schema)
    return  json_schema_file_object
