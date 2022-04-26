"""Lite local runtime runs agents locally with limited setup, like no MQ service and no defaults agents.

The local runtime requires Docker Swarm to run robust long-running services with a set of configured services.
"""
import logging
from typing import List
from typing import Optional

import click
import docker
import tenacity
from docker.models import services as docker_models_services

from ostorlab import exceptions
from ostorlab.assets import asset as base_asset
from ostorlab.cli import console as cli_console, dumpers
from ostorlab.cli import docker_requirements_checker
from ostorlab.cli import install_agent
from ostorlab.runtimes import definitions
from ostorlab.runtimes import runtime
from ostorlab.runtimes.lite_local import agent_runtime
from ostorlab.utils import volumes

NETWORK_PREFIX = 'ostorlab_lite_local_network'

logger = logging.getLogger(__name__)
console = cli_console.Console()

ASSET_INJECTION_AGENT_DEFAULT = 'agent/ostorlab/inject_asset'


class UnhealthyService(exceptions.OstorlabError):
    """A service by the runtime is considered unhealthy."""


class AgentNotInstalled(exceptions.OstorlabError):
    """Agent image not installed."""


class AgentNotHealthy(exceptions.OstorlabError):
    """Agent not healthy."""


def _has_container_image(agent: definitions.AgentSettings):
    """Check if container image is available"""
    return agent.container_image is not None


def _is_service_type_run(service: docker_models_services.Service) -> bool:
    """Checks if the service should run once or should be continuously running.

    Args:
        service: Docker service.

    Returns:
        Bool indicating if the service is run-once or long-running.
    """
    return service.attrs['Spec']['TaskTemplate']['RestartPolicy']['Condition'] == 'none'


class LiteLocalRuntime(runtime.Runtime):
    """Lite Local runtime runs agents locally using Docker Swarm.
    Lite Local runtime starts all the agents listed in the `AgentRunDefinition`, and then injects the target asset.
    """

    def __init__(self, scan_id: str, bus_url: str, bus_vhost: str, bus_management_url: str,
                 bus_exchange_topic: str, network: str, redis_url: str) -> None:
        """Set runtime attributes.

        Args:
            scan_id: Provided scan identifier, will be used to define the runtime name.
            bus_url: Bus URL, may contain credentials.
            bus_vhost: Bus virtual host, common default is / but none is provided here.
            bus_management_url: Bus management URL, typically runs on a separate port over https.
            bus_exchange_topic: Bus exchange topic.
            network: Docker network name to attach to.
            redis_url: Redis URL.
        """
        super().__init__()

        if not all([scan_id, bus_url, bus_vhost, bus_management_url, bus_exchange_topic, network, redis_url]):
            raise ValueError('Missing required fields.')

        self.scan_id = scan_id
        self._bus_url = bus_url
        self._bus_vhost = bus_vhost
        self._bus_management_url = bus_management_url
        self._bus_exchange_topic = bus_exchange_topic
        self._network = network
        self._redis_url = redis_url

        if not docker_requirements_checker.is_docker_installed():
            console.error('Docker is not installed.')
            raise click.exceptions.Exit(2)
        elif not docker_requirements_checker.is_user_permitted():
            console.error('User does not have permissions to run docker.')
            raise click.exceptions.Exit(2)
        elif not docker_requirements_checker.is_docker_working():
            console.error('Error using docker.')
            raise click.exceptions.Exit(2)
        else:
            if not docker_requirements_checker.is_swarm_initialized():
                docker_requirements_checker.init_swarm()
            self._docker_client = docker.from_env()

    @property
    def name(self) -> str:
        """Lite Local runtime instance name."""
        return self.scan_id

    @property
    def network(self) -> str:
        """Lite Local runtime network name.

        Returns:
            Lite Local runtime network name.
        """
        return self._network

    def can_run(self, agent_group_definition: definitions.AgentGroupDefinition) -> bool:
        """Checks if the runtime can run the provided agent run definition.

        Args:
            agent_group_definition: Agent and Agent group definition.

        Returns:
            Always true for the moment as the lite local runtime doesn't have restrictions on what it can run.
        """
        del agent_group_definition
        return True

    def scan(self, title: str, agent_group_definition: definitions.AgentGroupDefinition,
             assets: Optional[List[base_asset.Asset]]) -> None:
        """Start scan on asset using the provided agent run definition.

        The scan takes care of starting all the scan required services, ensuring they are healthy, starting all the
         agents, ensuring they are healthy and then injects the target asset.

        Args:
            title: Scan title
            agent_group_definition: Agent run definition defines the set of agents and how agents are configured.
            assets: the target asset to scan.

        Returns:
            None
        """
        try:
            console.info('Starting agents')
            self._start_agents(agent_group_definition)
            console.info('Checking agents are healthy')
            is_healthy = self._check_agents_healthy()
            if is_healthy is False:
                raise AgentNotHealthy()
            if assets is not None:
                console.info('Injecting assets')
                self._inject_assets(assets=assets)
        except AgentNotHealthy:
            console.error('Agent not starting')
            self.stop(self.scan_id)
        except AgentNotInstalled as e:
            console.error(f'Agent {e} not installed')
            self.stop(self.scan_id)
        except agent_runtime.MissingAgentDefinitionLabel as e:
            console.error(f'Missing agent definition {e}. This is probably due to building the image directly with'
                          f' docker instead of `ostorlab agent build` command')
            self.stop(self.scan_id)

    def stop(self, scan_id: str) -> None:
        """Remove a service (scan) belonging to universe with scan_id(Universe Id).

        Args:
            scan_id: The id of the scan to stop.
        """

        stopped_services = []
        stopped_network = []
        stopped_configs = []
        client = docker.from_env()
        services = client.services.list()
        for service in services:
            service_labels = service.attrs['Spec']['Labels']
            logger.debug('comparing %s and %s', service_labels.get(
                'ostorlab.universe'), scan_id)
            if service_labels.get('ostorlab.universe') == scan_id:
                stopped_services.append(service)
                service.remove()

        networks = client.networks.list()
        for network in networks:
            network_labels = network.attrs['Labels']
            if network_labels is not None and network_labels.get('ostorlab.universe') == scan_id:
                logger.debug('removing network %s', network_labels)
                stopped_network.append(network)
                network.remove()

        configs = client.configs.list()
        for config in configs:
            config_labels = config.attrs['Spec']['Labels']
            if config_labels.get('ostorlab.universe') == scan_id:
                logger.debug('removing config %s', config_labels)
                stopped_configs.append(config)
                config.remove()

        if stopped_services or stopped_network or stopped_configs:
            console.success('All scan components stopped.')

    def _check_agents_healthy(self):
        """Checks if an agent is healthy."""
        return self._are_agents_ready()

    def _start_agents(self, agent_group_definition: definitions.AgentGroupDefinition):
        """Starts all the agents as list in the agent run definition."""
        for agent in agent_group_definition.agents:
            self._start_agent(agent, extra_configs=[])

    def _start_agent(self, agent: definitions.AgentSettings,
                     extra_configs: Optional[List[docker.types.ConfigReference]] = None,
                     extra_mounts: Optional[List[docker.types.Mount]] = None
                     ) -> None:
        """Start agent based on provided definition.

        Args:
            agent: An agent definition containing all the settings of how agent should run and what arguments to pass.
        """
        logger.info('starting agent %s with %s', agent.key, agent.args)

        if _has_container_image(agent) is False:
            raise AgentNotInstalled(agent.key)

        runtime_agent = agent_runtime.AgentRuntime(agent,
                                                   self.name,
                                                   self._docker_client,
                                                   self._bus_url,
                                                   self._bus_vhost,
                                                   self._bus_management_url,
                                                   self._bus_exchange_topic,
                                                   self._redis_url
                                                   )
        agent_service = runtime_agent.create_agent_service(self.network, extra_configs, extra_mounts)

        if agent.replicas > 1:
            # Ensure the agent service had to
            # TODO(alaeddine): Check if sleep if really needed and if it is, implement a parallel way to start agents
            #  and scale them.
            # time.sleep(10)
            self._scale_service(agent_service, agent.replicas)

    @tenacity.retry(stop=tenacity.stop_after_attempt(20),
                    wait=tenacity.wait_exponential(multiplier=1, max=12),
                    # return last value and don't raise RetryError exception.
                    retry_error_callback=lambda lv: lv.outcome.result(),
                    retry=tenacity.retry_if_result(lambda v: v is False))
    def _is_service_healthy(self, service: docker_models_services.Service, replicas=None) -> bool:
        """Checks if a docker service is healthy by checking all tasks status."""
        logger.debug('checking Spec service %s', service.name)
        try:
            if not replicas:
                replicas = service.attrs['Spec']['Mode']['Replicated']['Replicas']
            return replicas == len([task for task in service.tasks() if task['Status']['State'] == 'running'])
        except docker.errors.NotFound:
            return False

    def _list_agent_services(self):
        """List the services of type agents. All agent service must start with agent_."""
        services = self._docker_client.services.list(
            filters={'label': f'ostorlab.universe={self.name}'})
        for service in services:
            if service.name.startswith('agent_'):
                yield service

    def _inject_assets(self, assets: List[base_asset.Asset]):
        """Injects the scan target assets."""

        contents = {}
        for i, asset in enumerate(assets):
            contents[f'asset.binproto_{i}'] = asset.to_proto()
            contents[f'selector.txt_{i}'] = asset.selector.encode()

        volumes.create_volume(f'asset_{self.name}', contents)

        inject_asset_agent_settings = definitions.AgentSettings(key=ASSET_INJECTION_AGENT_DEFAULT,
                                                                restart_policy='none')
        self._start_agent(agent=inject_asset_agent_settings,
                          extra_mounts=[
                              docker.types.Mount(
                                  target='/asset', source=f'asset_{self.name}', type='volume'
                              )])

    def _scale_service(self, service: docker_models_services.Service, replicas: int) -> None:
        """Calling scale directly on the service causes an API error. This is a workaround that simulates refreshing
         the service object, then calling the scale API."""
        for s in self._docker_client.services.list():
            if s.name == service.name:
                s.scale(replicas)

    @tenacity.retry(stop=tenacity.stop_after_attempt(20),
                    wait=tenacity.wait_exponential(multiplier=1, max=20),
                    # return last value and don't raise RetryError exception.
                    retry_error_callback=lambda lv: lv.outcome.result(),
                    retry=tenacity.retry_if_result(lambda v: v is False))
    def list(self, **kwargs):
        raise NotImplementedError()

    def _are_agents_ready(self, fail_fast=True) -> bool:
        """Checks that all agents are ready and healthy while taking into account the run type of agent
         (once vs long-running)."""
        logger.info('listing services ...')
        agent_services = list(self._list_agent_services())
        for service in agent_services:
            logger.info('checking %s ...', service.name)
            if not _is_service_type_run(service):
                if self._is_service_healthy(service):
                    logger.info('agent service %s is healthy', service.name)
                else:
                    logger.error('agent service %s is not healthy', service.name)
                    if fail_fast:
                        return False
        return True

    def install(self) -> None:
        """Installs the default agents.

        Returns:
            None
        """
        install_agent.install(agent_key=ASSET_INJECTION_AGENT_DEFAULT)
    def dump_vulnz(self, scan_id: int, dumper: dumpers.VulnzDumper):
        """Dump vulnerabilities to a file in a specific format.
            Returns:
            None
        """
        pass
