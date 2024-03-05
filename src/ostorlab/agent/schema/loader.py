"""Agent and Agent Group loader helper methods that handles schema validation and safe loading."""

import io
import pathlib

import ruamel.yaml

from ostorlab.agent.schema import validator

from typing import Dict, Any

AGENT_SPEC_PATH = pathlib.Path(__file__).parent / "agent_schema.json"
AGENT_GROUP_SPEC_PATH = pathlib.Path(__file__).parent / "agent_group_schema.json"
TARGET_GROUP_SPEC_PATH = pathlib.Path(__file__).parent / "target_group_schema.json"


def _load_spec_yaml(file: io.TextIOWrapper, spec: pathlib.Path) -> Dict[str, Any]:
    """Loads file based on spec"""
    with open(spec, "r", encoding="utf8") as schema_specs:
        yaml_def_validator = validator.Validator(schema_specs)
        yaml_def_validator.validate(file)
        file.seek(0)
        yaml = ruamel.yaml.YAML(typ="safe")
        agent_def: Dict[str, Any] = yaml.load(file)
        return agent_def


def load_agent_yaml(file: io.TextIOWrapper) -> Dict[str, Any]:
    """Loads and validates agent yaml definition file.

    Args:
        file: Yaml definition file.

    Returns:
        Parsed yaml dict.
    """

    spec = AGENT_SPEC_PATH
    return _load_spec_yaml(file, spec)


def load_agent_group_yaml(file: io.TextIOWrapper) -> Dict[str, Any]:
    """Loads and validates agent group yaml definition file.

    Args:
        file: Yaml definition file.

    Returns:
        Parsed yaml dict.
    """
    spec = AGENT_GROUP_SPEC_PATH
    return _load_spec_yaml(file, spec)


def load_target_group_yaml(file: io.TextIOWrapper) -> Dict[str, Any]:
    """Loads and validates target group yaml definition file.

    Args:
        file: Yaml definition file.

    Returns:
        Parsed yaml dict.
    """
    spec = TARGET_GROUP_SPEC_PATH
    return _load_spec_yaml(file, spec)
