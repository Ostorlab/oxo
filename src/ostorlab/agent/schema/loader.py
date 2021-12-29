"""Agent and Agent Group loader helper methods that handles schema validation and safe loading."""
import io
import pathlib
from typing import Dict

import ruamel.yaml

from ostorlab.agent.schema import validator

AGENT_SPEC_PATH = pathlib.Path(__file__).parent / 'agent_schema.json'
AGENT_GROUP_SPEC_PATH = pathlib.Path(__file__).parent / 'agent_group_schema.json'


def load_agent_yaml(file: io.FileIO) -> Dict:
    """Loads and validates agent yaml definition file.

    Args:
        file: Yaml definition file.

    Returns:
        Parsed yaml dict.
    """

    with open(AGENT_SPEC_PATH, 'r', encoding='utf8') as agent_spec:
        yaml_def_validator = validator.Validator(agent_spec)
        yaml_def_validator.validate(file)
        file.seek(0)
        yaml = ruamel.yaml.YAML(typ='safe')
        agent_def = yaml.load(file)
        return agent_def


def load_agent_group_yaml(file: io.FileIO) -> Dict:
    """Loads and validates agent gorup yaml definition file.

    Args:
        file: Yaml definition file.

    Returns:
        Parsed yaml dict.
    """
    with open(AGENT_GROUP_SPEC_PATH, 'r', encoding='utf8') as agent_grop_spec:
        yaml_def_validator = validator.Validator(agent_grop_spec)
        yaml_def_validator.validate(file)
        file.seek(0)
        yaml = ruamel.yaml.YAML(typ='safe')
        agent_def = yaml.load(file)
        return agent_def
