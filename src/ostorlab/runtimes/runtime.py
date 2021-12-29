"""Runtime are in charge of running scan as defines by a set of agents, agent group and a target asset."""
import abc
import dataclasses
from typing import List, Iterable, Optional, Dict, Any,TextIO

import ruamel.yaml

from ostorlab import assets
from ostorlab.agent.schema import validator
from ostorlab.utils import schemas


@dataclasses.dataclass
class AgentDefinition:
    """Data class holding attributes of an agent."""
    name: str
    path: str = None
    container_image: str = None
    args: Iterable = ()
    constraints: List[str] = None
    mounts: Optional[List[str]] = None
    restart_policy: str = 'any'
    mem_limit: int = None
    open_ports: Optional[Dict[int, int]] = None


@dataclasses.dataclass
class AgentInstanceSettings:
    """Agent instance lists the settings of running instance of an agent."""
    bus_url: str
    bus_exchange_topic: str
    args: List[Any] = dataclasses.field(default_factory=list)
    constraints: List[str] = None
    mounts: Optional[List[str]] = None
    restart_policy: str = 'any'
    mem_limit: int = None
    open_ports: Optional[Dict[int, int]] = None
    replicas: int = 1
    healthcheck_host: str = '0.0.0.0'
    healthcheck_port: int = 5000


@dataclasses.dataclass
class AgentGroupDefinition:
    """Data class holding the attributes of an agent."""
    agents: List[AgentInstanceSettings]


    @classmethod
    def from_file(cls, group: TextIO):
        """Construct AgentGroupDefinition from yaml file.

        Args:
            group : agent group .yaml file.
        """
        with open(schemas.AGENT_GROUP_SPEC_PATH, 'r') as agentgrp_spec:
            validator_object = validator.Validator(agentgrp_spec)
        yaml_parser = ruamel.yaml.YAML(typ='safe')
        agentgroup_def = yaml_parser.load(group)

        try:
            validator_object.validate(group)
        except validator.ValidationError:
            raise validator.ValidationError

        agents_definitions = []
        for agent in agentgroup_def['agents']:
            agent_def = AgentDefinition(agent['name'])
            for k, v in agent.items():
                setattr(agent_def, k, v)
            agents_definitions.append(agent_def)
        
        return cls(agents_definitions)


@dataclasses.dataclass
class AgentRunDefinition:
    """Data class defining scan run agent composition and configuration."""
    agents: List[AgentInstanceSettings]
    agent_groups: List[AgentGroupDefinition]

    @property
    def applied_agents(self) -> List[AgentInstanceSettings]:
        """The list of applicable agents. The list is composed of both defined agent and agent groups.

        Returns:
            List of agents used in the current run definition.
        """
        agents = []
        agents.extend(self.agents)
        for group in self.agent_groups:
            agents.extend(group.agents)
        return agents


class Runtime(abc.ABC):
    """Runtime is in charge of preparing the environment to trigger a scan."""

    @abc.abstractmethod
    def can_run(self, agent_run_definition: AgentRunDefinition) -> bool:
        """Checks if the runtime is capable of running the provided agent run definition.

        Args:
            agent_run_definition: The agent run definition from a set of agents and agent groups.

        Returns:
            True if can run, false otherwise.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def scan(self, agent_run_definition: AgentRunDefinition, asset: assets.Asset) -> None:
        """Triggers a scan using the provided agent run definition and asset target.

        Args:
            agent_run_definition: The agent run definition from a set of agents and agent groups.
            asset: The scan target asset.

        Returns:
            None
        """
        raise NotImplementedError()
