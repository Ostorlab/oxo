"""Tests for the validation of Yaml configuration files against json schema files."""

import io

import pytest

from ostorlab.agent.schema import validator


def testYamlValidation_whenItIsCorrect_noRaise(json_schema_file):
    """Unit test for the method that validates a yaml configuration file against a json schema.
    Case where the yaml configuration file is valid.
    """

    valid_yaml_data = """
        name: "Agent1"
        description: "Agent1 Description should be here"
        image: "some/path/to/the/image"
        source: "https://github.com/"
        durability: "development"
        restrictions:
        - "restriction1"
        - "restriction2"
        in_selectors:
        - "in_selector1"
        - "in_selector2"
        out_selectors:
        - "out_selector1"
        - "out_selector2"
        restart_policy: "none"
        args:
        - name: port
          type: number
        - name: schema
          type: string
    """

    with io.StringIO(valid_yaml_data) as yaml_data_file:
        validator_object = validator.Validator(json_schema_file)

        try:
            validator_object.validate(yaml_data_file)
        except validator.ValidationError:
            pytest.fail("ValidationError shouldn't be expected.")
        except validator.SchemaError:
            pytest.fail("SchemaError shouldn't be expected.")


def testYamlValidation_whenArgsAreMissingAnyRequiredFiled_raisesValidationError(json_schema_file):
    """Unit test for the method that validates an agent group yaml configuration file against a json schema.
    Case where the yaml configuration file is valid.
    """

    invalid_yaml_data = """
        name: "Agent1"
        description: "Agent1 Description should be here"
        image: "some/path/to/the/image"
        source: 3
        durability: "development"
        restrictions:
        - "restriction1"
        - "restriction2"
        in_selectors:
        - "in_selector1"
        - "in_selector2"
        out_selectors:
        - "out_selector1"
        - "out_selector2"
        restart_policy: "none"
        args:
        - name: port
          description: "Target that doesn't specify port will use this argument to set the target port."
          value: 443
        - type: string
          description: "Target that doesn't specify a schema will use this argument."
          value: https
    """
    validator_object = validator.Validator(json_schema_file)
    yaml_data_file = io.StringIO(invalid_yaml_data)

    with pytest.raises(validator.ValidationError) as exc_info:
        validator_object.validate(yaml_data_file)

    assert exc_info.type is validator.ValidationError


def testAgentGroupYamlValidation_whenItIsCorrect_noRaise(agent_group_json_schema_file):
    """Unit test for the method that validates a yaml configuration file against a json schema.
    Case where the yaml configuration file is invalid (args are missing required fields).
    """

    valid_yaml_data = """
        kind: "AgentGroup"
        description: "Agent group definition for asset autodiscovery."
        agents:
        - args: [{name: "arg1", type: string}]
          key: agent/ostorlab/whatweb
        - args: []
          key: agent/ostorlab/wappalyzer
    """
    with io.StringIO(valid_yaml_data) as yaml_data_file:
        validator_object = validator.Validator(agent_group_json_schema_file)

        try:
            validator_object.validate(yaml_data_file)
        except validator.ValidationError:
            pytest.fail("ValidationError shouldn't be expected.")
        except validator.SchemaError:
            pytest.fail("SchemaError shouldn't be expected.")


def testAgentGroupYamlValidation_whenAgentArgsAreWrongAndAgentKeyIsMissing_raisesValidationError(agent_group_json_schema_file):
    """Unit test for the method that validates an agent group yaml configuration file against a json schema.
    Case where the yaml configuration file is invalid (agent args are wrong and key is missing).
    """

    invalid_yaml_data = """
        kind: "AgentGroup"
        description: "Agent group definition for asset autodiscovery."
        agents:
        - args: [{name: "arg1"}]
        - args: [{type: "number"}]
          key: agent/ostorlab/wappalyzer
    """

    validator_object = validator.Validator(agent_group_json_schema_file)
    yaml_data_file = io.StringIO(invalid_yaml_data)

    with pytest.raises(validator.ValidationError) as exc_info:
        validator_object.validate(yaml_data_file)

    assert exc_info.type is validator.ValidationError


def testYamlValidation_whenSourceParamDoesNotRespectURLPattern_raisesValidationError(json_schema_file):
    """Unit test for the method that validates a yaml configuration file against a json schema.
    Case where the yaml configuration file is invalid : The parameter 'source' should be a URL instead of a number.
    """

    invalid_yaml_data = """
        name: "Agent1"
        description: "Agent1 Description should be here"
        image: "some/path/to/the/image"
        source: 3
        durability: "development"
        restrictions:
        - "restriction1"
        - "restriction2"
        in_selectors:
        - "in_selector1"
        - "in_selector2"
        out_selectors:
        - "out_selector1"
        - "out_selector2"
        restart_policy: "none"
    """
    validator_object = validator.Validator(json_schema_file)
    yaml_data_file = io.StringIO(invalid_yaml_data)

    with pytest.raises(validator.ValidationError) as exc_info:
        validator_object.validate(yaml_data_file)

    assert exc_info.type is validator.ValidationError


def testValidatorInit_whenSchemaIsInvalidTypeParamIsMisspelled_raisesSchemaError():
    """Unit test for the init of the validator class with a invalid schema.
    The type is misspelled : 'strg' instead of 'string'.
    """

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

    with pytest.raises(validator.SchemaError) as exc_info:
        _ = validator.Validator(json_schema_file_object)

    assert exc_info.type is validator.SchemaError
