"""Definitions of the fixtures that will be shared among multiple tests.
"""

from io import StringIO, FileIO
import pytest

@pytest.fixture
def json_schema_file() -> FileIO:
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


@pytest.fixture
def agent_json_spec() -> FileIO:
    """Agent Specification as a Json file object

    Returns:
      agent_spec_json_file_object : a file object of the json schema file.

    """
    agent_json_specification = """
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

            "version": {
                "type": "string",
                "maxLength": 512
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
                "maxLength": 1024, 
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
                "maxLength": 1024,
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
            }, 
            
            "portmap":{
                "type": "object",
                "properties": {
                    "port_src": { "type": "number" },  
                    "port_dst": { "type": "number" }
                }
            }, 

            "agentArgument":{
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "maxLength": 2048
                    },
                    "type": {
                        "type": "string",
                        "maxLength": 2048
                    },
                    "description": { "type": "string" },
                    "default_value": {
                        "type": "string",
                        "contentEncoding": "base64"
                    }

                }       
            }
        },

        "required": ["name", "version", "durability", "restrictions", "in_selectors", "out_selectors", "restart_policy"]
    }
    """
    
    agent_spec_json_file_object =  StringIO(agent_json_specification)
    return  agent_spec_json_file_object

@pytest.fixture
def agentGroup_json_spec() -> FileIO:
    """AgentGroup Specification as a Json file object

    Returns:
      agentGroup_spec_json_file_object : a file object of the json schema file.

    """
    agentGroup_json_specification = """
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
            "kind": {
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

            "restart_policy":{
                "type": "string",
                "maxLength": 1024,
                "enum": ["run_once", "always_restart"]
            },

            "restrictions": {
                "$ref": "#/CustomTypes/ArrayOfStrings"
            },

            "constraints":{ 
                "$ref": "#/CustomTypes/ArrayOfStrings"
            },


            "agents":{
                "type": "array",
                "items": {
                    "type": "object", 
                    "properties":{
                        "name": { "type": "string" },
                        "args": {"type": "array"},
                        "items":{
                            "type": "object"
                        }
                    }
                }       
            }, 

            "agentGroupArgument":{
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "maxLength": 2048
                    },
                    "type": {
                        "type": "string",
                        "maxLength": 2048
                    },
                    "description": { "type": "string" },
                    "value": { "type": "string" }
                }       
            }
        },

        "required": ["kind", "description", "agents"]
    }
    """
    agentGroup_spec_json_file_object =  StringIO(agentGroup_json_specification)
    return  agentGroup_spec_json_file_object


