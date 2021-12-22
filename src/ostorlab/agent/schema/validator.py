"""Validation of Yaml configuration files against json schema files.

Uses the jsonschema library to validate the yaml files.
Uses the ruamel.yaml for parssing the Yaml files.

    Typical usage example:
    validator = Validator(yaml_file_object, json_schema_file_object)
    validator.validate()
"""
import json
from io import FileIO
from jsonschema import validate
from jsonschema import exceptions
import ruamel.yaml

class OstorlabValidationError(Exception):
    """Wrapper Exception for the ValidationError produced by jsonschema's validate method.
    """

class OstorlabSchemaError(Exception):
    """Wrapper Exception for the SchemaError produced by jsonschema's validate method.
    """

class Validator():
    """Creates validator that checks yaml files with a json schema.

    Attributes:
        yaml_data: Parsed yaml data with ruamel.yaml parser.
        _json_schema: Parsed json schema.
    """

    def __init__(self, json_schema_file_object: FileIO):
        """Inits Validator class.

        Args:
            yaml_file_object: A file object of the Yaml configuration file.
            json_schema_file_object: A file object of the Json schema file.
        """
        self._json_schema = json.load(json_schema_file_object)


    def validate(self, yaml_file_object):
        """ Validates a yaml file against a json schema .

        Raises:
            OstorlabValidationError if the validation did not pass well.
            OstorlabSchemaError if the Schema is not valid.
        """
        yaml = ruamel.yaml.YAML(typ='safe')
        yaml_data = yaml.load(yaml_file_object)

        try:
            validate(instance=yaml_data, schema=self._json_schema)
        except exceptions.ValidationError as e:
            raise OstorlabValidationError("Validation did not pass well.") from e
        except exceptions.SchemaError as e:
            raise OstorlabSchemaError("Schema is invalid.") from e