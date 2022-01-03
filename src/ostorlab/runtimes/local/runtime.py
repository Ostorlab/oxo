"""Local runtime runs agents locally.

The local runtime requires Docker Swarm to run robust long-running services with a set of configured services, like
a local RabbitMQ.
"""
import logging
import socket
from typing import List
from typing import Optional

import docker
import requests
import tenacity
from docker.models import services as docker_models_services
from docker.types import services as docker_types_services

from ostorlab import exceptions
from ostorlab.assets import asset as base_asset
from ostorlab.runtimes import definitions
from ostorlab.runtimes import runtime
from ostorlab.runtimes.local.services import mq
from ostorlab.utils import strings as strings_utils

NETWORK = 'ostorlab_local_network'
HEALTHCHECK_HOST = '0.0.0.0'
HEALTHCHECK_PORT = '5000'

logger = logging.getLogger(__name__)

ASSET_INJECTION_AGENT_DEFAULT = 'agent/ostor/inject_asset'


class UnhealthyService(exceptions.OstorlabError):
    """A service by the runtime is considered unhealthy."""


def _is_agent_status_ok(ip: str) -> bool:
    """Agent are expected to expose a healthcheck service on port 5000 that returns status code 200 and `OK` response.

    Args:
        ip: The agent IP address.

    Returns:
        True if the agent is healthy, false otherwise.
    """
    status_ok = False
    try:
        status_ok = requests.get(f'http://{ip}:5000/status').text == 'OK'
    except requests.exceptions.ConnectionError:
        logger.error('unable to connect to %s', ip)
    return status_ok


def _get_task_ips(service: docker_models_services.Service) -> List[str]:
    """Returns list of IP addresses assigned to the tasks of a docker service.

    Args:
        service: docker service.

    Returns:
        List of IP addresses.
    """
    # current implementation supports only one task per service.
    logger.info('getting ips for task %s', service.name)
    try:
        ips = socket.gethostbyname_ex(f'tasks.{service.name}')
        logger.info('found ips %s for task %s', ips, service.name)
        return ips[2]
    except socket.gaierror:
        return []


def _is_service_type_run(service: docker_models_services.Service) -> bool:
    """Checks if the service should run once or should be continuously running.

    Args:
        service: Docker service.

    Returns:
        Bool indicating if the service is run-once or long-running.
    """
    return service.attrs['Spec']['TaskTemplate']['RestartPolicy']['Condition'] == 'none'


class LocalRuntime(runtime.Runtime):
    """Local runtime runes agents locally using Docker Swarm.
    Local runtime starts a Vanilla RabbitMQ service, starts all the agents listed in the `AgentRunDefinition`, checks
    their status and then inject the target asset.
    """

    def __init__(self, name: Optional[str] = None, network: str = NETWORK) -> None:
        super().__init__()
        self._name = name or strings_utils.random_string(6)
        self._network = network
        self._mq_service: Optional[mq.LocalRabbitMQ] = None
        # TODO(alaeddine): inject docker client to support more complex use-cases.
        self._docker_client = docker.from_env()

    @property
    def name(self) -> str:
        """Local runtime instance name."""
        return self._name

    def can_run(self, agent_group_definition: definitions.AgentGroupDefinition) -> bool:
        """Checks if the runtime can run the provided agent run definition.

        Args:
            agent_group_definition: Agent and Agent group definition.

        Returns:
            Always true for the moment as the local runtime don't have restrictions on what it can run.
        """
        del agent_group_definition
        return True

    def scan(self, agent_group_definition: definitions.AgentGroupDefinition, asset: base_asset.Asset) -> None:
        """Start scan on asset using the provided agent run definition.

        The scan takes care of starting all the scan required services, ensuring they are healthy, starting all the
         agents, ensuring they are healthy and then injects the target asset.

        Args:
            agent_group_definition: Agent run definition defines the set of agents and how agents are configured.
            asset: the target asset to scan.

        Returns:
            None
        """
        self._create_network()
        self._start_services()
        self._check_services_healthy()
        self._start_agents(agent_group_definition)
        self._check_agents_healthy(agent_group_definition)
        self._inject_asset(asset)

    def _create_network(self):
        """Creates a docker swarm network where all services and agents can communicates."""
        if any(network.name == self._network for network in self._docker_client.networks.list()):
            logger.warning('network already exists.')
        else:
            logger.info('creating private network %s', self._network)
            return self._docker_client.networks.create(
                name=self._network,
                driver='overlay',
                attachable=True,
                labels={'ostorlab.universe': self._name},
                check_duplicate=True
            )

    def _start_services(self):
        """Start all the local runtime services."""
        self._start_mq_service()

    def _start_mq_service(self):
        """Start a local rabbitmq service."""
        self._mq_service = mq.LocalRabbitMQ(name=self._name, network=self._network)
        self._mq_service.start()

    def _check_services_healthy(self):
        """Check if the rabbitMQ service is running and healthy."""
        if self._mq_service is None or self._mq_service.is_healthy is False:
            raise UnhealthyService('MQ service is unhealthy.')

    def _start_agents(self, agent_group_definition: definitions.AgentGroupDefinition):
        """Starts all the agents as list in the agent run definition."""
        for agent in agent_group_definition.agents:
            agent_instance_settings_proto = agent.to_raw_proto()
            docker_config = self._docker_client.configs.create(name=f'agent_{agent.key}_{self._name}',
                                                               data=agent_instance_settings_proto)
            config_reference = docker.types.ConfigReference(config_id=docker_config.id,
                                                              config_name=f'agent_{agent.key}_{self._name}',
                                                              filename='/tmp/settings.binproto')
            self._start_agent(agent, [config_reference])

    def _start_agent(self, agent: definitions.AgentSettings,
                     extra_configs: Optional[List[docker.types.ConfigReference]] = None) -> None:
        """Start agent based on provided definition.

        Args:
            agent: An agent definition containing all the settings of how agent should run and what arguments to pass.
        """
        logger.info('starting agent %s with %s', agent.key, agent.args)
        # Port published with ingress mode can't be used with dnsrr mode
        if agent.open_ports:
            endpoint_spec = docker_types_services.EndpointSpec(
                ports={p.destination_port: p.source_port for p in agent.open_ports})
        else:
            endpoint_spec = docker_types_services.EndpointSpec(mode='dnsrr')

        agent.bus_url = self._mq_service.url
        agent.bus_exchange_topic = f'ostorlab_topic_{self._name}'
        agent.healthcheck_host = HEALTHCHECK_HOST
        agent.healthcheck_port = HEALTHCHECK_PORT

        agent_service = self._docker_client.services.create(
            image=agent.container_image,
            networks=[self._network],
            env=[
                f'UNIVERSE={self._name}',
            ],
            name=f'{agent.container_image}_{self._name}',
            restart_policy=docker_types_services.RestartPolicy(condition=agent.restart_policy),
            mounts=agent.mounts,
            configs=extra_configs,
            labels={'ostorlab.universe': self._name},
            constraints=agent.constraints,
            endpoint_spec=endpoint_spec,
            resources=docker_types_services.Resources(mem_limit=agent.mem_limit))
        if agent.replicas > 1:
            # Ensure the agent service had to
            # TODO(alaeddine): Check if sleep if really needed and if it is, implement a parallel way to start agents
            #  and scale them.
            # time.sleep(10)
            self._scale_service(agent_service, agent.replicas)

    def _check_agents_healthy(self, agent_group_definition: definitions.AgentGroupDefinition):
        """Checks if an agent is healthy."""
        return self._are_agents_ready(agent_group_definition.agents)

    @tenacity.retry(stop=tenacity.stop_after_attempt(20),
                    wait=tenacity.wait_exponential(multiplier=1, max=12),
                    # return last value and don't raise RetryError exception.
                    retry_error_callback=lambda lv: lv.result(),
                    retry=tenacity.retry_if_result(lambda v: v is False))
    def _is_service_healthy(self, service: docker_models_services.Service, replicas=None) -> bool:
        """Checks if a docker service is healthy by checking all tasks status."""
        logger.info('checking service %s', service.name)
        if not replicas:
            replicas = service.attrs['Spec']['Mode']['Replicated']['Replicas']
        return replicas == len([task for task in service.tasks() if task['Status']['State'] == 'running'])

    @tenacity.retry(stop=tenacity.stop_after_attempt(20),
                    wait=tenacity.wait_exponential(multiplier=1, max=20),
                    # return last value and don't raise RetryError exception.
                    retry_error_callback=lambda lv: lv.result(),
                    retry=tenacity.retry_if_result(lambda v: v is False))
    def _are_agents_ready(self, agents: List[definitions.AgentSettings], fail_fast=True) -> bool:
        """Checks that all agents are ready and healthy while taking into account the run type of agent
         (once vs long-running)."""
        all_agents_healthy = True
        logger.info('listing services ...')
        agent_services = list(self._list_agent_services())
        if len(agent_services) < len(agents):
            logger.error('found %d, expecting %d', len(agent_services), len(agents))
            return False
        else:
            logger.info('found correct count of services')

        for service in agent_services:
            logger.info('checking %s ...', service.name)
            if not _is_service_type_run(service):
                if self._is_service_healthy(service):
                    task_healthy = False
                    container_ips = _get_task_ips(service)
                    healthy = any(_is_agent_status_ok(ip) for ip in container_ips)
                    # only a single task need to be healthy
                    task_healthy = task_healthy or healthy

                    # all agents need to be healthy
                    all_agents_healthy = all_agents_healthy and task_healthy
                    if fail_fast and not all_agents_healthy:
                        logger.error('agent health check %s is not healthy', service.name)
                        return False

                    logger.info('agent healthcheck of %s is %s', service.name, all_agents_healthy)
                else:
                    logger.error('agent service %s is not healthy', service.name)
                    if fail_fast and not all_agents_healthy:
                        return False
        return all_agents_healthy

    def _list_agent_services(self):
        """List the services of type agents. All agent service must start with agent_."""
        services = self._docker_client.services.list(filters={'label': f'ostorlab.universe={self._name}'})
        for service in services:
            if service.name.startswith('agent_'):
                yield service

    def _inject_asset(self, asset: base_asset.Asset):
        """Injects the scan target assets."""
        docker_config = self._docker_client.configs.create(name='asset',
                                                           data=asset.to_proto())
        config_reference = docker.types.ConfigReference(config_id=docker_config.id,
                                                        config_name='asset',
                                                        filename='/tmp/asset.binproto')
        inject_asset_agent_settings = definitions.AgentSettings(key=ASSET_INJECTION_AGENT_DEFAULT)
        self._start_agent(agent=inject_asset_agent_settings, extra_configs=[config_reference])

    def _scale_service(self, service: docker_models_services.Service, replicas: int) -> None:
        """Calling scale directly on the service causes an API error. This is a workaround that simulates refreshing
         the service object, then calling the scale API."""
        for s in self._docker_client.services.list():
            if s.name == service.name:
                s.scale(replicas)
