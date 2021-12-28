"""Tests for runtime classes responsible for running scans"""
import io

from ostorlab.runtimes import runtime

def testAgentGrpDefConstructionFromYaml_whenYamlValid_ConstructAgentGrpDefinitionWithoutError():
    """Unit test to check the construction of AgentGroupDefinition instances
    Case where agent group yaml definition is valid and object construction goes well.
    """
    valid_yaml = """
        kind: "AgentGroup1"
        description: "AgentGroup1 Should be here"
        image: "some/path/to/the/image"
        restart_policy: "always_restart"
        agents:
          - name: "AgentBigFuzzer"
            constraints:
              - "constraint1"
              - "constraint2"
            mounts:
              - "mount1"
              - "mount2"
            restart_policy: "always_restart"
            replicas: 0
            open_ports:
                src_port: 50000
                dest_port: 50300
            args:
                color: "red"
                speed: "slow" 
          - name: "AgentSmallFuzzer"
            constraints:
              - "constraint3"
              - "constraint4"
            mounts:
              - "mount3"
              - "mount4"
            restart_policy: "always_restart"
            replicas: 1
            open_ports:
                src_port: 50800
                dest_port: 55000
            args:
                color: "blue"
                speed: "fast" 
    """
    dummy_agent_def1 = runtime.AgentDefinition(
        name='AgentBigFuzzer',
        args={'color': 'red', 'speed': 'slow'},
        constraints=['constraint1', 'constraint2'],
        mounts=['mount1', 'mount2'],
        restart_policy='always_restart',
        open_ports={'src_port': 50000, 'dest_port': 50300},
        replicas=0
    )
    dummy_agent_def2 = runtime.AgentDefinition(
        name='AgentSmallFuzzer',
        args={'color': 'blue', 'speed': 'fast'},
        constraints=['constraint3', 'constraint4'],
        mounts=['mount3', 'mount4'],
        restart_policy='always_restart',
        open_ports={'src_port': 50800, 'dest_port': 55000},
        replicas=1,
    )
    dummy_agents = [dummy_agent_def1, dummy_agent_def2]
    agent_grp_def = runtime.AgentGroupDefinition([])
    with io.StringIO(valid_yaml) as valid_yaml_def:
        agent_grp_def = agent_grp_def.from_file(valid_yaml_def)

    assert len(agent_grp_def.agents) == len(dummy_agents)
    assert agent_grp_def.agents == dummy_agents
