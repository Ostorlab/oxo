"""Runtime agent module gives access to methods to create the specific agent configurations & run the agent.

Usage
    agent_runtime = AgentRuntime(agent_settings, runtime_name, docker_client, mq_service)
    agent_service = agent_runtime.create_agent_service(network_name, extra_configs)
"""
from typing import List, Optional
import docker
from docker.types import services as docker_types_services
import io

from ostorlab.runtimes.local import runtime
from ostorlab.runtimes import definitions
from ostorlab.agent import definitions as agent_definitions
from ostorlab.runtimes.local.services import mq



class AgentRuntime:
    """Class to consolidate the agent settings and agent default definition, and create the agent service."""

    def __init__(self,
                 agent_settings: definitions.AgentSettings,
                 runtime_name: str,
                 docker_client: docker.DockerClient,
                 mq_service: mq.LocalRabbitMQ) -> None:
        """Constructs all the necessary attributes for the object.

        Args:
            agent: an agent definition containing all the settings of how agent should run and what arguments to pass.
            runtime_name: local runtime instance name.
            docker_client: docker client.
        """
        self._docker_client = docker_client
        self.agent = agent_settings
        self.image_name = agent_settings.container_image.split(':', maxsplit=1)[0]
        self.runtime_name = runtime_name
        self.mq_service = mq_service
        self.update_agent_settings()

    def create_settings_config(self) -> docker.types.ConfigReference:
        """Create a docker configuration of the  agent settings.

        Returns:
            docker ConfigReference of the settings configuration
        """
        agent_instance_settings_proto = self.agent.to_raw_proto()
        config_name = f'config_settings_{self.image_name}_{self.runtime_name}'
        docker_config = self._docker_client.configs.create(name=config_name,
                                                           labels={'ostorlab.universe': self.runtime_name},
                                                           data=agent_instance_settings_proto)
        return docker.types.ConfigReference(config_id=docker_config.id,
                                            config_name=config_name,
                                            filename='/tmp/settings.binproto')

    def create_definition_config(self) -> docker.types.ConfigReference:
        """Create a docker configuration of the  agent definition.

        Returns:
            docker configuration reference of the agent defintion configuration.
        """
        agent_definition = self._docker_client.images.get(self.agent.container_image).labels.get('agent_definition')
        config_name = f'config_definition_{self.image_name}__{self.runtime_name}'
        docker_config = self._docker_client.configs.create(name=config_name,
                                                           labels={'ostorlab.universe': self.runtime_name},
                                                           data=str.encode(agent_definition))
        return docker.types.ConfigReference(config_id=docker_config.id,
                                            config_name=config_name,
                                            filename='/tmp/ostorlab.yaml')

    def create_agent_definition_from_label(self) -> agent_definitions.AgentDefinition:
        """Read the agent yaml definition from the docker image labels.

        Returns:
            the agent defintion.
        """
        docker_image = self._docker_client.images.get(self.agent.container_image)
        yaml_definition_string = docker_image.labels.get('agent_definition')
        with io.StringIO(yaml_definition_string) as file:
            agent_definition = agent_definitions.AgentDefinition.from_yaml(file)
            return agent_definition

    def update_agent_settings(self) -> None:
        """Update agent settings with values from the local runtime."""
        self.agent.bus_url = self.mq_service.url
        self.agent.bus_exchange_topic = f'ostorlab_topic_{self.runtime_name}'
        self.agent.bus_management_url = self.mq_service.management_url
        self.agent.bus_vhost = self.mq_service.vhost
        self.agent.healthcheck_host = runtime.HEALTHCHECK_HOST
        self.agent.healthcheck_port = runtime.HEALTHCHECK_PORT


    def create_docker_healthchek(self) -> docker.types.Healthcheck:
        """Create a docker healthcheck configuration for for the agent service.

        Returns:
            docker healthcheck configuration.
        """
        # wait 2s and check max 5 times with 0.5s between each check.
        healthcheck = docker.types.Healthcheck(test=['CMD', 'ostorlab', 'agent', 'healthcheck'],
                                               retries=runtime.HEALTHCHECK_RETRIES,
                                               timeout=runtime.HEALTHCHECK_TIMEOUT,
                                               start_period=runtime.HEALTHCHECK_START_PERIOD,
                                               interval=runtime.HEALTHCHECK_INTERVAL, )
        return healthcheck

    def create_agent_service(self,
                            network_name: str,
                            extra_configs: Optional[List[docker.types.ConfigReference]] = None
                            ) -> docker.models.services.Service:
        """Create the agent service.

        Args:
            network_name: network name to attach the service to.
            extra_configs: list of docker ConfigReferences that will be exposed to the service.

        Returns:
            the agent docker service.
        """
        agent_definition = self.create_agent_definition_from_label()
        self.agent.open_ports = self.agent.open_ports or agent_definition.open_ports
        if self.agent.open_ports:
            endpoint_spec = docker_types_services.EndpointSpec(
                ports={p.destination_port: p.source_port for p in self.agent.open_ports})
        else:
            endpoint_spec = docker_types_services.EndpointSpec(mode='dnsrr')

        extra_configs.append(self.create_settings_config())
        extra_configs.append(self.create_definition_config())

        mounts = self.agent.mounts or agent_definition.mounts
        constraints = self.agent.constraints or agent_definition.constraints
        mem_limit = self.agent.mem_limit or agent_definition.mem_limit
        restart_policy = self.agent.restart_policy or agent_definition.restart_policy

        service_name = self.agent.container_image.replace(':', '_').replace('.','') + '_' + self.runtime_name
        agent_service = self._docker_client.services.create(
            image=self.agent.container_image,
            networks=[network_name],
            env=[
                f'UNIVERSE={self.runtime_name}',
            ],
            name=service_name,
            restart_policy=docker_types_services.RestartPolicy(condition=restart_policy),
            mounts=mounts,
            healthcheck=self.create_docker_healthchek(),
            labels={'ostorlab.universe': self.runtime_name},
            configs=extra_configs,
            constraints=constraints,
            endpoint_spec=endpoint_spec,
            resources=docker_types_services.Resources(mem_limit=mem_limit))

        return agent_service
