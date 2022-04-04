"""Runtime agent module gives access to methods to create the specific agent configurations & run the agent.

Usage
    agent_runtime = AgentRuntime(agent_settings, runtime_name, docker_client, mq_service, redis_service)
    agent_service = agent_runtime.create_agent_service(network_name, extra_configs)
"""
import io
import logging
from typing import List, Optional

import docker
from docker import constants
from docker import errors
from docker.types import services as docker_types_services

from ostorlab import configuration_manager
from ostorlab import exceptions
from ostorlab.agent import definitions as agent_definitions
from ostorlab.runtimes import definitions
from ostorlab.runtimes.local.services import mq
from ostorlab.runtimes.local.services import redis

logger = logging.getLogger(__name__)

MOUNT_VARIABLES = {
    '$CONFIG_HOME': str(configuration_manager.OSTORLAB_PRIVATE_DIR)
}

HEALTHCHECK_HOST = '0.0.0.0'
HEALTHCHECK_PORT = 5000
SECOND = 1000000000
HEALTHCHECK_RETRIES = 5
HEALTHCHECK_TIMEOUT = 10 * SECOND
HEALTHCHECK_START_PERIOD = 2 * SECOND
HEALTHCHECK_INTERVAL = 2 * SECOND


class Error(exceptions.OstorlabError):
    """Base Error."""


class MissingAgentDefinitionLabel(Error):
    """Agent definition label is missing from the agent image. This is likely due to the agent built directly with a
     docker command and not agent build."""


def _parse_mount_string_windows(string):
    """Handles parsing mounts on Windows OS."""
    parts = string.split(':')
    if len(parts) == 1:
        # This supposes only having a target like /root.
        return docker_types_services.Mount(target=parts[0], source=None)
    elif len(parts) == 2:
        # This supposes having a source linux style and target. Like /var/run/docker.sock:/var/run/docker.sock.
        target = parts[1]
        source = parts[0]
        mount_type = 'volume'
        if source.startswith('/'):
            # Paths likes /var/run/docker.sock map to //var/run/docker.sock on windows.
            source = f'/{source}'
            mount_type = 'bind'
        return docker_types_services.Mount(target, source, read_only=False, type=mount_type)
    elif len(parts) == 3:
        # This supposes two cases. First case is windows style with linux, like C:/Users/bob:/root. The second
        # case is /root:/root:ro
        if parts[2] in ('ro', 'rw', 'z', 'Z'):
            target = parts[1]
            source = parts[0]
            mount_type = 'volume'
            if source.startswith('/'):
                # Paths likes /var/run/docker.sock map to //var/run/docker.sock on windows.
                source = f'/{source}'
                mount_type = 'bind'
            read_only = not parts[2] == 'rw'
            return docker_types_services.Mount(target, source, read_only=read_only, type=mount_type)
        else:
            target = parts[2]
            source = ':'.join(parts[:2])
            source = source.replace('\\', '/')
            mount_type = 'bind'
            return docker_types_services.Mount(target, source, read_only=False, type=mount_type)
    elif len(parts) == 4:
        # This covers the case C:/Users/bob:/root:ro
        target = parts[2]
        source = ':'.join(parts[:2])
        source = source.replace('\\', '/')
        mount_type = 'bind'
        read_only = not (len(parts) == 3 or parts[3] == 'rw')
        return docker_types_services.Mount(target, source, read_only=read_only, type=mount_type)
    else:
        raise errors.InvalidArgument(
            f'Invalid mount format "{string}"'
        )


def _parse_mount_string_unix(string):
    """Handles parsing of mounts on Unix OS like Linux, Cygwin and MacOS."""
    parts = string.split(':')
    if len(parts) > 3:
        raise errors.InvalidArgument(
            f'Invalid mount format "{string}"'
        )
    if len(parts) == 1:
        return docker_types_services.Mount(target=parts[0], source=None)
    else:
        target = parts[1]
        source = parts[0]
        mount_type = 'volume'
        if source.startswith('/'):
            mount_type = 'bind'
        read_only = not (len(parts) == 2 or parts[2] == 'rw')
        return docker_types_services.Mount(target, source, read_only=read_only, type=mount_type)


def _parse_mount_string(string):
    """This is a fix to a bug in the Docker Python API by monkey patching the buggy method.

    The method is knowingly not supporting Windows. Until a fix PR is merged, we are hot patching the method to handle
    windows paths with : like C:/Users/bob/:/root.
    """
    if constants.IS_WINDOWS_PLATFORM:
        return _parse_mount_string_windows(string)
    else:
        return _parse_mount_string_unix(string)


docker_types_services.Mount.parse_mount_string = _parse_mount_string


class AgentRuntime:
    """Class to consolidate the agent settings and agent default definition, and create the agent service."""

    def __init__(self,
                 agent_settings: definitions.AgentSettings,
                 runtime_name: str,
                 docker_client: docker.DockerClient,
                 mq_service: mq.LocalRabbitMQ,
                 redis_service: redis.LocalRedis
                 ) -> None:
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
        self.redis_service = redis_service
        self.update_agent_settings()

    def create_settings_config(self) -> docker.types.ConfigReference:
        """Create a docker configuration of the  agent settings.

        Returns:
            docker ConfigReference of the settings configuration
        """
        agent_instance_settings_proto = self.agent.to_raw_proto()
        config_name = f'config_settings_{self.image_name}_{self.runtime_name}'

        try:
            settings_config = self._docker_client.configs.get(config_name)
            logging.warning('found existing config %s, config will removed', config_name)
            settings_config.remove()
        except docker.errors.NotFound:
            logging.debug('all good, config %s is new', config_name)

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

        try:
            settings_config = self._docker_client.configs.get(config_name)
            logging.warning('found existing config %s, config will removed', config_name)
            settings_config.remove()
        except docker.errors.NotFound:
            logging.debug('all good, config %s is new', config_name)

        docker_config = self._docker_client.configs.create(name=config_name,
                                                           labels={'ostorlab.universe': self.runtime_name},
                                                           data=str.encode(agent_definition))
        return docker.types.ConfigReference(config_id=docker_config.id,
                                            config_name=config_name,
                                            filename='/tmp/ostorlab.yaml')

    def create_agent_definition_from_label(self) -> agent_definitions.AgentDefinition:
        """Read the agent yaml definition from the docker image labels.

        Returns:
            the agent definition.
        """
        docker_image = self._docker_client.images.get(self.agent.container_image)
        yaml_definition_string = docker_image.labels.get('agent_definition')
        if yaml_definition_string is None:
            raise MissingAgentDefinitionLabel(f'agent definition label is missing from image {docker_image.tags[0]}')
        with io.StringIO(yaml_definition_string) as file:
            agent_definition = agent_definitions.AgentDefinition.from_yaml(file)
            return agent_definition

    def update_agent_settings(self) -> None:
        """Update agent settings with values from the local runtime."""
        self.agent.bus_url = self.mq_service.url
        self.agent.bus_exchange_topic = f'ostorlab_topic_{self.runtime_name}'
        self.agent.bus_management_url = self.mq_service.management_url
        self.agent.bus_vhost = self.mq_service.vhost
        self.agent.healthcheck_host = HEALTHCHECK_HOST
        self.agent.healthcheck_port = HEALTHCHECK_PORT
        self.agent.redis_url = self.redis_service.url

    def create_docker_healthchek(self) -> docker.types.Healthcheck:
        """Create a docker healthcheck configuration for the agent service.

        Returns:
            docker healthcheck configuration.
        """
        # wait 2s and check max 5 times with 0.5s between each check.
        healthcheck = docker.types.Healthcheck(test=['CMD', 'ostorlab', 'agent', 'healthcheck'],
                                               retries=HEALTHCHECK_RETRIES,
                                               timeout=HEALTHCHECK_TIMEOUT,
                                               start_period=HEALTHCHECK_START_PERIOD,
                                               interval=HEALTHCHECK_INTERVAL, )
        return healthcheck

    def replace_variable_mounts(self, mounts: List[str]):
        """Replace path variables for the container mounts

        Args:
            mounts: List of src:dst paths to mount
        """

        replaced_mounts = []
        for mount in mounts:
            for mount_variable, mount_value in MOUNT_VARIABLES.items():
                mount = mount.replace(mount_variable, mount_value)
            replaced_mounts.append(mount)
        return replaced_mounts

    def create_agent_service(self,
                             network_name: str,
                             extra_configs: Optional[List[docker.types.ConfigReference]] = None,
                             extra_mounts: Optional[List[docker.types.Mount]] = None
                             ) -> docker.models.services.Service:
        """Create the docker agent service with proper configs and policies.

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

        configs = []
        configs.append(self.create_settings_config())
        configs.append(self.create_definition_config())
        if extra_configs is not None:
            configs.extend(extra_configs)

        mounts = self.agent.mounts or agent_definition.mounts
        mounts = self.replace_variable_mounts(mounts)
        if extra_mounts is not None:
            mounts.extend(extra_mounts)

        constraints = self.agent.constraints or agent_definition.constraints
        mem_limit = self.agent.mem_limit or agent_definition.mem_limit
        restart_policy = self.agent.restart_policy or agent_definition.restart_policy

        service_name = self.agent.container_image.replace(':', '_').replace('.', '') + '_' + self.runtime_name
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
            configs=configs,
            constraints=constraints,
            endpoint_spec=endpoint_spec,
            resources=docker_types_services.Resources(mem_limit=mem_limit))

        return agent_service
