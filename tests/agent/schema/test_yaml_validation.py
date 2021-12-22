"""Tests for the validation of Yaml configuration files against json schema files.
"""

import io

import pytest

from src.ostorlab.agent.schema.validator import Validator
from src.ostorlab.agent.schema.validator import ValidationError, SchemaError


def testYamlValidation_whenItIsCorrect_noRaise(json_schema_file):
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

    with io.StringIO(valid_yaml_data) as yaml_data_file:
        validator = Validator(json_schema_file)

        try:
            validator.validate(yaml_data_file)
        except ValidationError:
            pytest.fail("ValidationError shouldn't be expected.")
        except SchemaError:
            pytest.fail("SchemaError shouldn't be expected.")


def testYamlValidation_whenItIsWrong_raisesValidationError(json_schema_file):
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
    validator = Validator(json_schema_file)
    yaml_data_file = io.StringIO(invalid_yaml_data)

    with pytest.raises(ValidationError) as exc_info:
        validator.validate(yaml_data_file)

    assert exc_info.type is ValidationError


def testYamlValidation_whenSchemaIsInvalid_raisesSchemaError():
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
    json_schema_file_object = io.StringIO(invalid_json_schema)

    yaml_data_file = io.StringIO(valid_yaml_data)
    validator = Validator(json_schema_file_object)

    with pytest.raises(SchemaError) as exc_info:
        validator.validate(yaml_data_file)

    assert exc_info.type is SchemaError
