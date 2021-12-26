"""Tests for the validation of Json specifications for Agent & AgentGroup."""

from pathlib import Path
import io

import pytest

from ostorlab.agent.schema import validator

OSTORLAB_ROOT_DIR = Path(__file__).parent.parent.parent.parent
# is this the correct way to do it ?
AGENT_SPEC_PATH = path = OSTORLAB_ROOT_DIR / 'src/ostorlab/agent/schema/agent_schema.json'  
AGENT_GROUP_SPEC_PATH = OSTORLAB_ROOT_DIR / 'src/ostorlab/agent/schema/agentGroup_schema.json'


def testAgentSpecValidation_whenDefinitionIsCorrect_noRaise():
    """Unit test to checks the validity of the Agent json-schema.
    Case where the Agent definition is valid.
    """

    valid_yaml_data = """
        name: "Agent1"
        version : 1.1.0
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
        restart_policy: "run_once"
        mem_limit: 4096
        portmap:
         port_src: 50001
         port_dst: 50200
        docker_file_path: "some/path/to/Dockerfile"
        docker_build_root: "/"
        agent_runner: "theAgentRunner"
        agent_path: "some/path/to/agent.py"
        agenArgument:
        - name: "agentArgumentName1"
          type: "string"
          description: "agentArgumentDescription1"
          default_value: "agentArgumentDefaultValue1"
        - name: "agentArgumentName2"
          type: "number"
          description: "agentArgumentDescription2"
          default_value: "42"
    """
    with open(AGENT_SPEC_PATH, 'r', encoding='utf8') as agent_json_spec:
        validator_object = validator.Validator(agent_json_spec)

    with io.StringIO(valid_yaml_data) as yaml_data_file:
        try:
            validator_object.validate(yaml_data_file)
        except validator.ValidationError:
            pytest.fail("ValidationError shouldn't be expected.")
        except validator.SchemaError:
            pytest.fail("SchemaError shouldn't be expected.")


def testAgentSpecValidation_whenVersionDoesNotRespectSemanticVersionning_raiseValidationError():
    """Unit test to checks the validity of the Agent json-schema.
    Case where the Agent definition is invalid.
    The version does not respect the semantic versionning : major.minor.release.
    """

    invalid_yaml_data = """
        name: "Agent1"
        version : 1.
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
        restart_policy: "run_once"
        mem_limit: 4096
        portmap:
         port_src: 50001
         port_dst: 50200
        docker_file_path: "some/path/to/Dockerfile"
        docker_build_root: "/"
        agent_runner: "theAgentRunner"
        agent_path: "some/path/to/agent.py"
        agenArgument:
        - name: "agentArgumentName1"
          type: "string"
          description: "agentArgumentDescription1"
          default_value: "agentArgumentDefaultValue1"
        - name: "agentArgumentName2"
          type: "number"
          description: "agentArgumentDescription2"
          default_value: "42"
    """
    with open(AGENT_SPEC_PATH, 'r', encoding='utf8') as agent_json_spec:
        validator_object = validator.Validator(agent_json_spec)    
    yaml_data_file = io.StringIO(invalid_yaml_data)

    with pytest.raises(validator.ValidationError) as exc_info:
        validator_object.validate(yaml_data_file)

    assert exc_info.type is validator.ValidationError


def testAgentGroupSpecValidation_whenDefinitionIsCorrect_noRaise():
    """Unit test to checks the validity of the AgentGroup json-schema.
    Case where the AgentGroup definition is valid.
    """

    valid_yaml_agent_group_data = """
        kind: "AgentGroup1"
        description: "AgentGroup1 Should be here"
        image: "some/path/to/the/image"
        restart_policy: "always_restart"
        restrictions:
        - "restriction1"
        - "restriction2"
        constraints:
        - "constraint1"
        - "constraint2"
        
        agents:
            - name: "AgentBigFuzzer"
              args:
               - color: "red"
                 speed: "slow" 
            - name: "AgentSmallFuzzer"
              args:
               - color: "blue"
                 speed: "fast"
        
        agentGroupArgument:
            - name: "agentGroupArgumentExample1"
              type: "string"
              description: "agentGroupArgumentDescription1"
              value: "agentGroupArgumentValue1"
            - name: "agentGroupArgumentExample2"
              type: "number"
              description: "agentGroupArgumentDescription2"
              value: "42"    
    """
    with open(AGENT_GROUP_SPEC_PATH, 'r', encoding='utf8') as agentGroup_json_spec:
        validator_object = validator.Validator(agentGroup_json_spec)

    with io.StringIO(valid_yaml_agent_group_data) as yaml_data_file:
        try:
            validator_object.validate(yaml_data_file)
        except validator.ValidationError:
            pytest.fail("ValidationError shouldn't be expected.")
        except validator.SchemaError:
            pytest.fail("SchemaError shouldn't be expected.")


def testAgentGroupSpecValidation_whenRequiredParamDescriptionIsMissing_raiseValidationError():
    """Unit test to checks the validity of the AgentGroup json-schema.
    Case where the AgentGroup definition is invalid : Required parameter description is missing.
    """

    invalid_yaml_agent_group_data = """
        kind: "AgentGroup1"
        image: "some/path/to/the/image"
        restart_policy: "always_restart"
        restrictions:
        - "restriction1"
        - "restriction2"
        constraints:
        - "constraint1"
        - "constraint2"
        
        agents:
            - name: "AgentBigFuzzer"
              args:
               - color: "red"
                 speed: "slow" 
            - name: "AgentSmallFuzzer"
              args:
               - color: "blue"
                 speed: "fast"

        agentGroupArgument:
            - name: "agentGroupArgumentExample1"
              type: "string"
              description: "agentGroupArgumentDescription1"
              value: "agentGroupArgumentValue1"
            - name: "agentGroupArgumentExample2"
              type: "number"
              description: "agentGroupArgumentDescription2"
              value: "42"

    """
    with open(AGENT_GROUP_SPEC_PATH, 'r', encoding='utf8') as agentGroup_json_spec:
        validator_object = validator.Validator(agentGroup_json_spec)
    yaml_data_file = io.StringIO(invalid_yaml_agent_group_data)

    with pytest.raises(validator.ValidationError) as exc_info:
        validator_object.validate(yaml_data_file)

    assert exc_info.type is validator.ValidationError
