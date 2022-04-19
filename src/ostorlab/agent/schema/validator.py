"""Validation of Yaml configuration files against json schema files.

    Typical usage example:
    validator = Validator(json_schema_file_object)
    validator.validate(yaml_file_object)
"""
import io
import json

import jsonschema
import ruamel.yaml

from ostorlab import exceptions


class Error(exceptions.OstorlabError):
    """Base Exception
    """


class ValidationError(Error):
    """Wrapper Exception for the ValidationError produced by jsonschema's validate method."""


class SchemaError(Error):
    """Wrapper Exception for the SchemaError produced by jsonschema's validate method."""


class Validator:
    """Creates validator that checks yaml files with a json schema."""

    def __init__(self, json_schema_file_object: io.FileIO):
        """Inits Validator class.

        Args:
            json_schema_file_object: A file object of the Json schema file.

        Raises:
            SchemaError: When the Json schema file in itself is not valid.
        """
        self._json_schema = json.load(json_schema_file_object)
        try:
            jsonschema.Draft202012Validator.check_schema(self._json_schema)
        except jsonschema.exceptions.SchemaError as e:
            raise SchemaError('Schema is invalid.') from e

    def validate(self, yaml_file_object):
        """ Validates a yaml file against a json schema .

        Args:
            yaml_file_object: A file object of the yaml configuration file we want to validate.
        Raises:
            ValidationError if the validation did not pass well.
            SchemaError if the Schema is not valid.
        """
        yaml = ruamel.yaml.YAML(typ='safe')
        yaml_data = yaml.load(yaml_file_object)

        try:
            jsonschema.validate(instance=yaml_data, schema=self._json_schema)
        except jsonschema.exceptions.ValidationError as e:
            raise ValidationError(f'Validation did not pass: {e.message} for field {".".join(e.schema_path)}.') from e
        except jsonschema.exceptions.SchemaError as e:
            raise SchemaError('Schema is invalid.') from e
