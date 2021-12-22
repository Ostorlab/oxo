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
from jsonschema.exceptions import ValidationError, SchemaError
import ruamel.yaml


class Validator():
    """Creates validator that checks yaml files with a json schema.

    Attributes:
        yaml_data: Parsed yaml data with ruamel.yaml parser.
        json_schema: Parsed json schema.
    """

    def __init__(self, yaml_file_object: FileIO, json_schema_file_object: FileIO):
        """Inits Validator class.

        Args:
            yaml_file_object: A file object of the Yaml configuration file.
            json_schema_file_object: A file object of the Json schema file.
        """
        self.json_schema = json.load(json_schema_file_object)

        yaml = ruamel.yaml.YAML(typ='safe')
        self.yaml_data = yaml.load(yaml_file_object)


    def validate(self):
        """ Validates a yaml file on a json schema using jsonschema library.
        Returns:
            True if it is valid
        Raises:
            OstorlabValidationError if the validation did not pass well.
            OstorlabSchemaError if the Schema is not valid.
        """
        try:
            validate(instance=self.yaml_data, schema=self.json_schema)
        except ValidationError:
            raise OstorlabValidationError("Validation did not pass well.")
        except SchemaError:
            raise OstorlabSchemaError("Schema is invalid.")



class OstorlabValidationError(Exception):
    """Wrapper Exception for the ValidationError produced by jsonschema's validate method.
    """

class OstorlabSchemaError(Exception):
    """Wrapper Exception for the SchemaError produced by jsonschema's validate method.
    """
