"""Agent and Agent group definitions and settings dataclasses."""
import dataclasses
import io
from typing import List, Optional

from ostorlab.agent.schema import loader
from ostorlab.runtimes.proto import agent_instance_settings_pb2


@dataclasses.dataclass
class Arg:
    """Data class holding a definition.

    The value is always bytes to support all arg values. The type is defined by the type attribute."""
    name: str
    type: str
    value: bytes


@dataclasses.dataclass
class PortMapping:
    """Data class defining a port mapping source to destination"""
    source_port: int
    destination_port: int


@dataclasses.dataclass
class AgentDefinition:
    """Data class holding attributes of an agent."""
    name: str
    in_selectors: List[str] = dataclasses.field(default_factory=list)
    out_selectors: List[str] = dataclasses.field(default_factory=list)
    args: List[Arg] = dataclasses.field(default_factory=list)
    constraints: List[str] = None
    mounts: Optional[List[str]] = None
    restart_policy: str = 'any'
    mem_limit: int = None
    open_ports: List[PortMapping] = dataclasses.field(default_factory=list)

    @classmethod
    def from_yaml(cls, file: io.FileIO) -> 'AgentDefinition':
        """Constructs an agent definition from a yaml definition file.

        Args:
            file: Yaml file.

        Returns:
            Agent definition.
        """
        definition = loader.load_agent_yaml(file)
        return cls(
            name=definition.get('name'),
            in_selectors=definition.get('in_selectors'),
            out_selectors=definition.get('out_selectors'),
            args=definition.get('args'),
            constraints=definition.get('constraints'),
            mounts=definition.get('mounts'),
            restart_policy=definition.get('restart_policy'),
            mem_limit=definition.get('mem_limit'),
            open_ports=definition.get('open_ports'),
        )


@dataclasses.dataclass
class AgentInstanceSettings:
    """Agent instance lists the settings of running instance of an agent."""
    bus_url: str
    bus_exchange_topic: str
    args: List[Arg] = dataclasses.field(default_factory=list)
    constraints: List[str] = dataclasses.field(default_factory=list)
    mounts: Optional[List[str]] = dataclasses.field(default_factory=list)
    restart_policy: str = 'any'
    mem_limit: Optional[int] = None
    open_ports: List[PortMapping] = dataclasses.field(default_factory=list)
    replicas: int = 1
    healthcheck_host: str = '0.0.0.0'
    healthcheck_port: int = 5000

    @classmethod
    def from_proto(cls, proto: bytes) -> 'AgentInstanceSettings':
        """Constructs an agent definition from a binary proto settings.

        Args:
            proto: binary proto settings file.

        Returns:
            AgentInstanceSettings object.
        """
        instance = agent_instance_settings_pb2.AgentInstanceSettings()
        instance.ParseFromString(proto)
        return cls(
            bus_url=instance.bus_url,
            bus_exchange_topic=instance.bus_exchange_topic,
            args=[Arg(
                name=a.name,
                type=a.type,
                value=a.value
            ) for a in instance.args],
            constraints=instance.constraints,
            mounts=instance.mounts,
            restart_policy=instance.restart_policy,
            mem_limit=instance.mem_limit,
            open_ports=[PortMapping(
                source_port=p.source_port,
                destination_port=p.destination_port
            ) for p in instance.open_ports],
            replicas=instance.replicas,
            healthcheck_host=instance.healthcheck_host,
            healthcheck_port=instance.healthcheck_port,
        )

    def to_raw_proto(self) -> bytes:
        """Transforms agent instance settings into a raw proto bytes.

        Returns:
            Bytes as a serialized proto.
        """
        instance = agent_instance_settings_pb2.AgentInstanceSettings()
        instance.bus_url = self.bus_url
        instance.bus_exchange_topic = self.bus_exchange_topic

        for arg in self.args:
            arg_instance = instance.args.add()
            arg_instance.name = arg.name
            arg_instance.type = arg.type
            arg_instance.value = arg.value

        instance.constraints.extend(self.constraints)
        instance.mounts.extend(self.mounts)
        instance.restart_policy = self.restart_policy
        if self.mem_limit is not None:
            instance.mem_limit = self.mem_limit

        for open_port in self.open_ports:
            open_port_instance = instance.open_ports.add()
            open_port_instance.source_port = open_port.source_port
            open_port_instance.destination_port = open_port.destination_port

        instance.replicas = self.replicas
        instance.healthcheck_host = self.healthcheck_host
        instance.healthcheck_port = self.healthcheck_port

        return instance.SerializeToString()


@dataclasses.dataclass
class AgentGroupDefinition:
    """Data class holding the attributes of an agent."""
    agents: List[AgentInstanceSettings]

    @classmethod
    def from_yaml(cls, group: io.FileIO):
        """Construct AgentGroupDefinition from yaml file.

        Args:
            group : agent group .yaml file.
        """
        agentgroup_def = loader.load_agent_group_yaml(group)
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
