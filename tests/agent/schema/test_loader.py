"""Tests for the validation of Json specifications for Agent & AgentGroup."""

import io

import pytest

from ostorlab.agent.schema import loader
from ostorlab.agent.schema import validator


def testAgentSpecValidation_whenDefinitionIsCorrect_noRaise():
    """Unit test to check the validity of the Agent json-schema.
    Case where the Agent definition is valid.
    """

    valid_yaml_data = """
        kind: Agent
        name: "agent"
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
        restart_policy: "any"
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
          type: ["string", "number", "boolean"]
          description: "agentArgumentDescription1"
          default_value: "agentArgumentDefaultValue1"
        - name: "agentArgumentName2"
          type: ["string", "number", "boolean"]
          description: "agentArgumentDescription2"
          default_value: 42
    """
    yaml_data_file = io.StringIO(valid_yaml_data)

    data = loader.load_agent_yaml(yaml_data_file)

    assert data['name'] == 'agent'
    assert data['version'] == '1.1.0'
    assert data['agenArgument'][1]['default_value'] == 42


def testAgentSpecValidation_whenVersionDoesNotRespectSemanticVersionning_raiseValidationError():
    """Unit test to checks the validity of the Agent json-schema.
    Case where the Agent definition is invalid.
    The version does not respect the semantic versionning : major.minor.release.
    """

    invalid_yaml_data = """
        name: "Agent"
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
        restart_policy: "any"
        mem_limit: 4096
        portmap:
         port_src: 50001
         port_dst: 50200
        docker_file_path: "some/path/to/Dockerfile"
        docker_build_root: "/"
        agent_runner: "theAgentRunner"
        agent_path: "some/path/to/agent.py"
        args:
        - name: "agentArgumentName1"
          type: ["string", "number", "boolean"]
          description: "agentArgumentDescription1"
          default_value: "agentArgumentDefaultValue1"
        - name: "agentArgumentName2"
          type: ["string", "number", "boolean"]
          description: "agentArgumentDescription2"
          default_value: 42
    """
    yaml_data_file = io.StringIO(invalid_yaml_data)

    with pytest.raises(validator.ValidationError):
        loader.load_agent_yaml(yaml_data_file)


def testAgentGroupSpecValidation_whenDefinitionIsCorrect_noRaise():
    """Unit test to checks the validity of the AgentGroup json-schema.
    Case where the AgentGroup definition is valid.
    """

    valid_yaml_agent_group_data = """
        kind: "AgentGroup"
        description: "AgentGroup1 Should be here"
        image: "some/path/to/the/image"
        restart_policy: "any"
        restrictions:
        - "restriction1"
        - "restriction2"
        constraints:
        - "constraint1"
        - "constraint2"

        agents:
            - name: "AgentBigFuzzer"
              key: agent/testorg/bigfuzzer
              args:
               - color: "red"
                 speed: "slow"
                 name: "arg1"
                 type: "string"
            - name: "AgentSmallFuzzer"
              key: agent/testorg/smallfuzzer
              args:
               - color: "blue"
                 speed: "fast"
                 name: "arg2"
                 type: "string"

        agentGroupArgument:
            - name: "agentGroupArgumentExample1"
              type: ["string", "number", "boolean"]
              description: "agentGroupArgumentDescription1"
              value: "agentGroupArgumentValue1"
            - name: "agentGroupArgumentExample2"
              type: ["string", "number", "boolean"]
              description: "agentGroupArgumentDescription2"
              value: 42
    """
    yaml_data_file = io.StringIO(valid_yaml_agent_group_data)

    data = loader.load_agent_group_yaml(yaml_data_file)

    assert data['description'] == 'AgentGroup1 Should be here'


def testAgentGroupSpecValidation_whenRequiredParamDescriptionIsMissing_raiseValidationError():
    """Unit test to checks the validity of the AgentGroup json-schema.
    Case where the AgentGroup definition is invalid : Required parameter description is missing.
    """

    invalid_yaml_agent_group_data = """
        kind: "AgentGroup1"
        image: "some/path/to/the/image"
        restart_policy: "any"
        restrictions:
        - "restriction1"
        - "restriction2"
        constraints:
        - "constraint1"
        - "constraint2"

        agents:
            - name: "AgentBigFuzzer"
              key: agent/testorg/bigfuzzer
              args:
               - color: "red"
                 speed: "slow"
                 name: "arg1"
                 type: "string"
            - name: "AgentSmallFuzzer"
              key: agent/testorg/smallfuzzer
              args:
               - color: "blue"
                 speed: "fast"
                 name: "arg2"
                 type: "string"

        agentGroupArgument:
            - name: "agentGroupArgumentExample1"
              type: ["string", "number", "boolean"]
              description: "agentGroupArgumentDescription1"
              value: "agentGroupArgumentValue1"
            - name: "agentGroupArgumentExample2"
              type: "string"
              description: "agentGroupArgumentDescription2"
              value: 42

    """
    yaml_data_file = io.StringIO(invalid_yaml_agent_group_data)

    with pytest.raises(validator.ValidationError):
        loader.load_agent_group_yaml(yaml_data_file)
