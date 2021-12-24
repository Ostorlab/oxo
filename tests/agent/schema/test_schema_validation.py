"""Tests for the validation of Json specifications for Agent & AgentGroup.
"""

import io

import pytest

from src.ostorlab.agent.schema.validator import Validator
from src.ostorlab.agent.schema.validator import ValidationError, SchemaError


def testAgentSpecValidation_whenDefinitionIsCorrect_noRaise(agent_json_spec):
    """Unit test to checks the validity of the Agent json-schema.
    Case where the Agent definition is valid.

    Args:
      agent_json_spec:
        pytest fixture for the agent spec json file object.
    """

    valid_yaml_data = """
        name: Agent1
        version : 1.1.0
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
        validator = Validator(agent_json_spec)

        try:
            validator.validate(yaml_data_file)
        except ValidationError:
            pytest.fail("ValidationError shouldn't be expected.")
        except SchemaError:
            pytest.fail("SchemaError shouldn't be expected.")


def testAgentSpecValidation_whenDefinitionIsIncorrect_raiseValidationError(agent_json_spec):
    """Unit test to checks the validity of the Agent json-schema.
    Case where the Agent definition is invalid.

    Args:
      agentSpec_json_file:
        pytest fixture for the agent spec json file object.
    """

    # The version parameter is not respecting the convention : major.minor.revision .
    invalid_yaml_data = """
        name: Agent1
        version: 1.
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
    validator = Validator(agent_json_spec)
    yaml_data_file = io.StringIO(invalid_yaml_data)

    with pytest.raises(ValidationError) as exc_info:
        validator.validate(yaml_data_file)

    assert exc_info.type is ValidationError


def testAgentGroupSpecValidation_whenDefinitionIsCorrect_noRaise(agentGroup_json_spec):
    """Unit test to checks the validity of the AgentGroup json-schema.
    Case where the AgentGroup definition is valid.

    Args:
      agentGroup_json_spec:
        pytest fixture for the agentGroup spec json file object.
    """
    valid_yaml_agentGroup_data = """
        kind: AgentGroup1
        description: AgentGroup1 Should be here
        image: some/path/to/the/image
        restart_policy: always_restart
        restrictions:
        - restriction1
        - restriction2
        constraints:
        - constraint1
        - constraint2
        
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
         name: "agentGroupArgumentExample"
         type: "agentGroupArgumentTypeExample"
         description: "agentGroupArgumentDescription"
         value: "agentGroupArgumentValue"
    """
    validator = Validator(agentGroup_json_spec)

    with io.StringIO(valid_yaml_agentGroup_data) as yaml_data_file:
        try:
            validator.validate(yaml_data_file)
        except ValidationError:
            pytest.fail("ValidationError shouldn't be expected.")
        except SchemaError:
            pytest.fail("SchemaError shouldn't be expected.")


def testAgentGroupSpecValidation_whenDefinitionIsIncorrect_raiseValidationError(agentGroup_json_spec):
    """Unit test to checks the validity of the AgentGroup json-schema.
    Case where the AgentGroup definition is invalid.

    Args:
      agentGroup_json_spec:
        pytest fixture for the agentGroup spec json file object.
    """
    # The required parameter 'description' is missing.
    invalid_yaml_agentGroup_data = """
        kind: AgentGroup1
        image: some/path/to/the/image
        restart_policy: always_restart
        restrictions:
        - restriction1
        - restriction2
        constraints:
        - constraint1
        - constraint2
        
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
         name: "agentGroupArgumentExample"
         type: "agentGroupArgumentTypeExample"
         description: "agentGroupArgumentDescription"
         value: "agentGroupArgumentValue"       
    """
    validator = Validator(agentGroup_json_spec)
    yaml_data_file = io.StringIO(invalid_yaml_agentGroup_data)

    with pytest.raises(ValidationError) as exc_info:
        validator.validate(yaml_data_file)

    assert exc_info.type is ValidationError