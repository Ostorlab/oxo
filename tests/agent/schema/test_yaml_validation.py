"""Tests for the validation of Yaml configuration files against json schema files.
"""

from io import StringIO, FileIO

import pytest

from src.ostorlab.agent.schema.validator import Validator
from src.ostorlab.agent.schema.validator import OstorlabValidationError, OstorlabSchemaError


def testYamlValidation_WhenItIsCorrect_NoRaise(json_schema_file: FileIO):
    """Unit test for the method that validates a yaml configuration file against a json schema.
    Case where the yaml configuration file is valid.

    Args:
      json_schema_file:
        py test fixture for the json schema file object.
    """

    valid_yaml_data = """
        name: Agent1
        description: Agent1 Description should be here
        image: some/path/to/the/image
        source: https://github.com/
        durability: development
        restrictions: 
        - restriction1
        - restriction2
        in_selectors: 
        - in_selector1
        - in_selector2
        out_selectors:
        - out_selector1
        - out_selector2
        restart_policy: run_once
    """

    with StringIO(valid_yaml_data) as yaml_data_file:
        validator = Validator(yaml_data_file, json_schema_file)

        try:
            validator.validate()
        except OstorlabValidationError:
            pytest.fail("OstorlabValidationError shouldn't be expected.")
        except OstorlabSchemaError:
            pytest.fail("OstorlabSchemaError shouldn't be expected.")


def testYamlValidation_WhenItIsWrong_RaisesOstorlabValidationError(json_schema_file):
    """Unit test for the method that validates a yaml configuration file against a json schema.
    Case where the yaml configuration file is invalid.

    Args:
      json_schema_file:
        py test fixture for the json schema file object.
    """

    # source value bellow should be a URL instead of the given number 3.
    invalid_yaml_data = """
        name: Agent1
        description: Agent1 Description should be here
        image: some/path/to/the/image
        source: 3
        durability: development
        restrictions: 
        - restriction1
        - restriction2
        in_selectors: 
        - in_selector1
        - in_selector2
        out_selectors:
        - out_selector1
        - out_selector2
        restart_policy: run_once
    """

    with StringIO(invalid_yaml_data) as yaml_data_file:
        validator = Validator(yaml_data_file, json_schema_file)

    with pytest.raises(OstorlabValidationError) as exc_info:
        validator.validate()

    assert exc_info.type is OstorlabValidationError

def testYamlValidation_WhenSchemaIsInvalid_RaisesOstorlabSchemaError():
    """Unit test for the method that validates a yaml configuration file against a json schema.
    Case where the Json schema file is invalid.
    """

    valid_yaml_data = """
        name: Agent1
        description: Agent1 Description should be here
        image: some/path/to/the/image
        source: https://github.com/
        durability: development
        restrictions: 
        - restriction1
        - restriction2
        in_selectors: 
        - in_selector1
        - in_selector2
        out_selectors:
        - out_selector1
        - out_selector2
        restart_policy: run_once
    """

    # the invalid part : type : "strg".
    invalid_json_schema = """
        {
            "properties": {
                    "name": {
                        "type": "strg",
                        "maxLength": 2048
                    }
            }
        }
    """
    json_schema_file_object =  StringIO(invalid_json_schema)

    with StringIO(valid_yaml_data) as yaml_data_file:
        validator = Validator(yaml_data_file, json_schema_file_object)

    with pytest.raises(OstorlabSchemaError) as exc_info:
        validator.validate()

    assert exc_info.type is OstorlabSchemaError
