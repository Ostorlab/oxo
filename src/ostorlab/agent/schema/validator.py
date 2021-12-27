"""Validation of Yaml configuration files against json schema files.

    Typical usage example:
    validator = Validator(json_schema_file_object)
    validator.validate(yaml_file_object)
"""
import json
from io import FileIO
from jsonschema import validate, exceptions
from jsonschema import Draft202012Validator
import ruamel.yaml

VERSIONED_JSONSCHEMA_VALIDATOR = Draft202012Validator


class Error(Exception):
    """Base Exception
    """


class ValidationError(Error):
    """Wrapper Exception for the ValidationError produced by jsonschema's validate method.
    """


class SchemaError(Error):
    """Wrapper Exception for the SchemaError produced by jsonschema's validate method.
    """


class Validator:
    """Creates validator that checks yaml files with a json schema.
    """

    def __init__(self, json_schema_file_object: FileIO):
        """Inits Validator class.

        Args:
            json_schema_file_object: A file object of the Json schema file.

        Raises:
            SchemaError: When the Json schema file in itself is not valid.
        """
        self._json_schema = json.load(json_schema_file_object)
        try:
            VERSIONED_JSONSCHEMA_VALIDATOR.check_schema(self._json_schema)
        except exceptions.SchemaError as e:
            raise SchemaError("Schema is invalid.") from e

    def validate(self, yaml_file_object):
        """ Validates a yaml file against a json schema .

        Args:
            yaml_file_object: A file object of the yaml configuration file we want to validate.
        Raises:
            ValidationError if the validation did not pass well.
            SchemaError if the Schema is not valid.
        """
        yaml = ruamel.yaml.YAML(typ="safe")
        yaml_data = yaml.load(yaml_file_object)

        try:
            validate(instance=yaml_data, schema=self._json_schema)
        except exceptions.ValidationError as e:
            raise ValidationError("Validation did not pass well.") from e
        except exceptions.SchemaError as e:
            raise SchemaError("Schema is invalid.") from e
