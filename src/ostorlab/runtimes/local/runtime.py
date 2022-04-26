"""Local runtime runs agents locally.

The local runtime requires Docker Swarm to run robust long-running services with a set of configured services, like
a local RabbitMQ.
"""
import logging
from typing import List
from typing import Optional

import click
import docker
import rich
import sqlalchemy
import tenacity
from docker.models import services as docker_models_services
from rich import markdown
from rich import panel
from sqlalchemy import case

from ostorlab import exceptions
from ostorlab.assets import asset as base_asset
from ostorlab.cli import console as cli_console
from ostorlab.cli import docker_requirements_checker
from ostorlab.cli import dumpers
from ostorlab.cli import install_agent
from ostorlab.runtimes import definitions
from ostorlab.runtimes import runtime
from ostorlab.runtimes.local import agent_runtime
from ostorlab.runtimes.local import log_streamer
from ostorlab.runtimes.local.models import models
from ostorlab.runtimes.local.services import mq
from ostorlab.runtimes.local.services import redis
from ostorlab.utils import risk_rating
from ostorlab.utils import styles
from ostorlab.utils import volumes

NETWORK_PREFIX = 'ostorlab_local_network'

logger = logging.getLogger(__name__)
console = cli_console.Console()

ASSET_INJECTION_AGENT_DEFAULT = 'agent/ostorlab/inject_asset'
TRACKER_AGENT_DEFAULT = 'agent/ostorlab/tracker'
LOCAL_PERSIST_VULNZ_AGENT_DEFAULT = 'agent/ostorlab/local_persist_vulnz'

DEFAULT_AGENTS = [
    ASSET_INJECTION_AGENT_DEFAULT,
    TRACKER_AGENT_DEFAULT,
    LOCAL_PERSIST_VULNZ_AGENT_DEFAULT
]


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


class LocalRuntime(runtime.Runtime):
    """Local runtime runs agents locally using Docker Swarm.
    Local runtime starts a Vanilla RabbitMQ service, starts all the agents listed in the `AgentRunDefinition`, checks
    their status and then inject the target asset.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__()
        del args, kwargs
        self.follow = []
        self._mq_service: Optional[mq.LocalRabbitMQ] = None
        self._redis_service: Optional[redis.LocalRedis] = None
        self._log_streamer = log_streamer.LogStream()
        self._scan_db: Optional[models.Scan] = None

    @property
    def name(self) -> str:
        """Local runtime instance name."""
        if self._scan_db is not None:
            return str(self._scan_db.id)
        else:
            raise ValueError('Scan not created yet')

    @property
    def network(self) -> str:
        """Local runtime network name.

        Returns:
            Local runtime network name.
        """
        return f'{NETWORK_PREFIX}_{self.name}'

    def can_run(self, agent_group_definition: definitions.AgentGroupDefinition) -> bool:
        """Checks if the runtime can run the provided agent run definition.

        Args:
            agent_group_definition: Agent and Agent group definition.

        Returns:
            Always true for the moment as the local runtime doesn't have restrictions on what it can run.
        """
        del agent_group_definition
        self._docker_checks()
        return True

    def _docker_checks(self):
        """checking the requirements (docker, swarm,permissions) for ostorlab."""
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
            console.info('Creating scan entry')
            if assets is None:
                assets_str='N/A'
            else:
                assets_str = f'{", ".join([str(asset) for asset in assets])}'
                # TODO(mohsinenar): we need to add support for storing multiple assets and rename this to target.
            self._scan_db = self._create_scan_db(asset=assets_str[:255], title=title)
            console.info('Creating network')
            self._create_network()
            console.info('Starting services')
            self._start_services()
            console.info('Checking services are healthy')
            self._check_services_healthy()

            console.info('Starting pre-agents')
            self._start_pre_agents()
            console.info('Checking pre-agents are healthy')
            is_healthy = self._check_agents_healthy()
            if is_healthy is False:
                raise AgentNotHealthy()

            console.info('Starting agents')
            self._start_agents(agent_group_definition)
            console.info('Checking agents are healthy')
            is_healthy = self._check_agents_healthy()
            if is_healthy is False:
                raise AgentNotHealthy()

            if assets is not None:
                self._inject_assets(assets)
            console.info('Updating scan status')
            self._update_scan_progress('IN_PROGRESS')

            console.info('Starting post-agents')
            self._start_post_agents()
            console.info('Checking post-agents are healthy')
            is_healthy = self._check_agents_healthy()
            if is_healthy is False:
                raise AgentNotHealthy()

            console.success('Scan created successfully')
        except AgentNotHealthy:
            console.error('Agent not starting')
            self.stop(self._scan_db.id)
            self._update_scan_progress('ERROR')
            self.stop(str(self._scan_db.id))
        except AgentNotInstalled as e:
            console.error(f'Agent {e} not installed')
            self.stop(str(self._scan_db.id))
        except UnhealthyService as e:
            console.error(f'Unhealthy service {e}')
            self.stop(str(self._scan_db.id))
        except agent_runtime.MissingAgentDefinitionLabel as e:
            console.error(f'Missing agent definition {e}. This is probably due to building the image directly with'
                          f' docker instead of `ostorlab agent build` command')
            self.stop(str(self._scan_db.id))

    def stop(self, scan_id: str) -> None:
        """Remove a service (scan) belonging to universe with scan_id(Universe Id).

        Args:
            scan_id: The id of the scan to stop.
        """
        try:
            int_scan_id = int(scan_id)
        except ValueError as e:
            console.error('Scan id must be an integer.')
            raise click.exceptions.Exit(2) from e

        logger.info('stopping scan id %s', scan_id)
        stopped_services = []
        stopped_network = []
        stopped_configs = []
        self._docker_checks()
        services = self._docker_client.services.list()
        for service in services:
            service_labels = service.attrs['Spec']['Labels']
            logger.info('comparing %s and %s', service_labels.get('ostorlab.universe'), scan_id)
            if service_labels.get('ostorlab.universe') == scan_id:
                stopped_services.append(service)
                service.remove()

        networks = self._docker_client.networks.list()
        for network in networks:
            network_labels = network.attrs['Labels']
            if network_labels is not None and network_labels.get('ostorlab.universe') == scan_id:
                logger.info('removing network %s', network_labels)
                stopped_network.append(network)
                network.remove()

        configs = self._docker_client.configs.list()
        for config in configs:
            config_labels = config.attrs['Spec']['Labels']
            if config_labels.get('ostorlab.universe') == scan_id:
                logger.info('removing config %s', config_labels)
                stopped_configs.append(config)
                config.remove()

        if stopped_services or stopped_network or stopped_configs:
            console.success('All scan components stopped.')

        database = models.Database()
        session = database.session
        scan = session.query(models.Scan).get(int_scan_id)
        if scan:
            scan.progress = 'STOPPED'
            session.commit()
            console.success('Scan stopped successfully.')
        else:
            console.info(f'Scan {scan_id} was not found.')

    def _create_scan_db(self, title: str, asset: str):
        """Persist the scan in the database"""
        models.Database().create_db_tables()
        return models.Scan.create(title=title, asset=asset)

    def _update_scan_progress(self, progress: str):
        """Update scan status to in progress"""
        database = models.Database()
        session = database.session
        scan = session.query(models.Scan).get(self._scan_db.id)
        scan.progress = progress
        session.commit()

    def _create_network(self):
        """Creates a docker swarm network where all services and agents can communicate."""
        if any(network.name == self.network for network in self._docker_client.networks.list()):
            logger.warning('network already exists.')
        else:
            logger.info('creating private network %s', self.network)
            return self._docker_client.networks.create(
                name=self.network,
                driver='overlay',
                attachable=True,
                labels={'ostorlab.universe': self.name},
                check_duplicate=True
            )

    def _start_services(self):
        """Start all the local runtime services."""
        self._start_mq_service()
        self._start_redis_service()

    def _start_mq_service(self):
        """Start a local rabbitmq service."""
        self._mq_service = mq.LocalRabbitMQ(name=self.name, network=self.network)
        self._mq_service.start()
        if 'mq' in self.follow:
            self._log_streamer.stream(self._mq_service.service)

    def _start_redis_service(self):
        """Start a local Redis service."""
        self._redis_service = redis.LocalRedis(name=self.name, network=self.network)
        self._redis_service.start()
        if 'redis' in self.follow:
            self._log_streamer.stream(self._redis_service.service)

    def _check_services_healthy(self):
        """Check if the rabbitMQ service is running and healthy."""
        if self._mq_service is None or self._mq_service.is_healthy is False:
            raise UnhealthyService('MQ service is unhealthy.')
        if self._redis_service is None or self._redis_service.is_healthy is False:
            raise UnhealthyService('Redis service is unhealthy.')

    def _check_agents_healthy(self):
        """Checks if an agent is healthy."""
        return self._are_agents_ready()

    def _start_agents(self, agent_group_definition: definitions.AgentGroupDefinition):
        """Starts all the agents as list in the agent run definition."""
        for agent in agent_group_definition.agents:
            self._start_agent(agent, extra_configs=[])

    def _start_pre_agents(self):
        """Starting pre-agents that must exist before other agents. This applies to all persistence
        agents that can start sending data at the start of the agent."""
        self._start_persist_vulnz_agent()

    def _start_post_agents(self):
        """Starting post-agents that must exist after other agents. This applies to the tracker
        that needs to monitor other agents."""
        self._start_tracker_agent()

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

        runtime_agent = agent_runtime.AgentRuntime(
            agent, self.name, self._docker_client, self._mq_service, self._redis_service)
        agent_service = runtime_agent.create_agent_service(self.network, extra_configs, extra_mounts)
        if agent.key in self.follow:
            self._log_streamer.stream(agent_service)

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
        services = self._docker_client.services.list(filters={'label': f'ostorlab.universe={self.name}'})
        for service in services:
            if service.name.startswith('agent_'):
                yield service

    def _start_tracker_agent(self):
        """Start the tracker agent to handle the scan lifecycle."""
        tracker_agent_settings = definitions.AgentSettings(key=TRACKER_AGENT_DEFAULT)
        self._start_agent(agent=tracker_agent_settings, extra_configs=[])

    def _start_persist_vulnz_agent(self):
        """Start the local persistence agent to dump vulnerabilities in the local config."""
        persist_vulnz_agent_settings = definitions.AgentSettings(
            key=LOCAL_PERSIST_VULNZ_AGENT_DEFAULT,
            mounts=[])
        self._start_agent(agent=persist_vulnz_agent_settings, extra_configs=[])

    def _inject_assets(self, assets: List[base_asset.Asset]):
        """Injects the scan target assets."""
        contents = {}
        for i, asset in enumerate(assets):
            console.info(f'Injecting asset: {asset}')
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

    def list(self, page: int = 1, number_elements: int = 10) -> List[runtime.Scan]:
        """Lists scans managed by runtime.

        Args:
            page: Page number for list pagination (default 1).
            number_elements: count of elements to show in the listed page (default 10).

        Returns:
            List of scan objects.
        """
        if page is not None:
            console.warning('Local runtime ignores scan list pagination')

        scans = {}
        database = models.Database()
        database.create_db_tables()
        session = database.session
        for s in session.query(models.Scan):
            scans[s.id] = runtime.Scan(
                id=s.id,
                asset=s.asset,
                created_time=s.created_time,
                progress=s.progress.value,
            )

        universe_ids = set()
        client = docker.from_env()
        services = client.services.list()

        for s in services:
            try:
                service_labels = s.attrs['Spec']['Labels']
                ostorlab_universe_id = service_labels.get('ostorlab.universe')
                if 'ostorlab.universe' in service_labels.keys() and ostorlab_universe_id not in universe_ids:
                    universe_ids.add(ostorlab_universe_id)
                    if ostorlab_universe_id.isnumeric() and int(ostorlab_universe_id) not in scans:
                        console.warning(f'Scan {ostorlab_universe_id} has not traced in DB.')
            except KeyError:
                logger.warning('The label ostorlab.universe do not exist.')

        return list(scans.values())

    @tenacity.retry(stop=tenacity.stop_after_attempt(20),
                    wait=tenacity.wait_exponential(multiplier=1, max=20),
                    # return last value and don't raise RetryError exception.
                    retry_error_callback=lambda lv: lv.outcome.result(),
                    retry=tenacity.retry_if_result(lambda v: v is False))
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
        for agent_key in DEFAULT_AGENTS:
            install_agent.install(agent_key=agent_key)

    def list_vulnz(self, scan_id: int):
        try:
            database = models.Database()
            session = database.session
            vulnerabilities = session.query(models.Vulnerability).filter_by(scan_id=scan_id). \
                order_by(models.Vulnerability.title).all()
            console.success('Vulnerabilities listed successfully.')
            vulnz_list = []
            for vulnerability in vulnerabilities:
                vulnz_list.append({
                    'id': str(vulnerability.id),
                    'risk_rating': styles.style_risk(vulnerability.risk_rating.value.upper()),
                    'cvss_v3_vector': vulnerability.cvss_v3_vector,
                    'title': vulnerability.title,
                    'short_description': markdown.Markdown(vulnerability.short_description),
                })

            columns = {
                'Id': 'id',
                'Title': 'title',
                'Risk rating': 'risk_rating',
                'CVSS V3 Vector': 'cvss_v3_vector',
                'Short Description': 'short_description',
            }
            title = f'Scan {scan_id}: Found {len(vulnz_list)} vulnerabilities.'
            console.table(columns=columns, data=vulnz_list, title=title)
        except sqlalchemy.exc.OperationalError:
            console.error(f'scan with id {scan_id} does not exist.')

    def _print_vulnerability(self, vulnerability):
        """Print vulnerability details"""
        if vulnerability is None:
            return

        vulnz_list = [
            {'id': str(vulnerability.id),
             'risk_rating': styles.style_risk(vulnerability.risk_rating.value.upper()),
             'cvss_v3_vector': vulnerability.cvss_v3_vector,
             'title': vulnerability.title,
             'short_description': markdown.Markdown(vulnerability.short_description),
             }
        ]
        columns = {
            'Id': 'id',
            'Title': 'title',
            'Risk rating': 'risk_rating',
            'CVSS V3 Vector': 'cvss_v3_vector',
            'Short Description': 'short_description',
        }
        title = f'Describing vulnerability {vulnerability.id}'
        console.table(columns=columns, data=vulnz_list, title=title)
        rich.print(panel.Panel(markdown.Markdown(vulnerability.description), title='Description'))
        rich.print(panel.Panel(markdown.Markdown(vulnerability.recommendation), title='Recommendation'))
        rich.print(panel.Panel(markdown.Markdown(vulnerability.technical_detail), title='Technical details'))

    def describe_vuln(self, scan_id: int, vuln_id: int):
        try:
            database = models.Database()
            session = database.session
            vulnerabilities = []
            if vuln_id is not None:
                vulnerability = session.query(models.Vulnerability).get(vuln_id)
                vulnerabilities.append(vulnerability)
            elif scan_id is not None:
                vulnerabilities = session.query(models.Vulnerability).filter_by(scan_id=scan_id). \
                    order_by(models.Vulnerability.title).all()
            for v in vulnerabilities:
                self._print_vulnerability(v)
            console.success('Vulnerabilities listed successfully.')
        except sqlalchemy.exc.OperationalError:
            console.error('Vulnerability / scan not Found.')

    def dump_vulnz(self, scan_id: int, dumper: dumpers.VulnzDumper):
        """Dump found vulnerabilities of a scan in a specific format."""
        database = models.Database()
        session = database.session
        severity_sort_logic = case(value=models.Vulnerability.risk_rating,
                                   whens=risk_rating.RATINGS_ORDER).label('severity')
        vulnerabilities = session.query(models.Vulnerability).filter_by(scan_id=scan_id). \
            order_by(severity_sort_logic).all()

        vulnz_list = []
        for vulnerability in vulnerabilities:
            vuln = {
                'id': vulnerability.id,
                'risk_rating': vulnerability.risk_rating.value,
                'cvss_v3_vector': vulnerability.cvss_v3_vector,
                'title': vulnerability.title,
                'short_description': vulnerability.short_description,
                'description': vulnerability.description,
                'recommendation': vulnerability.recommendation,
                'technical_detail': vulnerability.technical_detail,
            }
            vulnz_list.append(vuln)
        dumper.dump(vulnz_list)
        console.success(f'{len(vulnerabilities)} Vulnerabilities saved to  : {dumper.output_path}')
