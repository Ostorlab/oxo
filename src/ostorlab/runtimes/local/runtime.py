"""Local runtime runs agents locally.

The local runtime requires Docker Swarm to run robust long-running services with a set of configured services, like
a local RabbitMQ.
"""

import logging
from concurrent import futures
from typing import Dict, List
from typing import Optional

import click
import docker
import rich
import sqlalchemy
import tenacity
from docker import errors as docker_errors
from docker.models import services as docker_models_services
from rich import markdown
from rich import panel
from sqlalchemy import case

from ostorlab import exceptions
from ostorlab.assets import asset as base_asset
from ostorlab.cli import console as cli_console
from ostorlab.cli import agent_fetcher
from ostorlab.cli import docker_requirements_checker
from ostorlab.cli import dumpers
from ostorlab.cli import install_agent
from ostorlab.runtimes import definitions
from ostorlab.runtimes import runtime
from ostorlab.runtimes.local import agent_runtime
from ostorlab.runtimes.local import log_streamer
from ostorlab.runtimes.local.models import models
from ostorlab.runtimes.local.services import jaeger
from ostorlab.runtimes.local.services import mq
from ostorlab.runtimes.local.services import redis
from ostorlab.utils import risk_rating
from ostorlab.utils import styles
from ostorlab.utils import volumes

NETWORK_PREFIX = "ostorlab_local_network"

logger = logging.getLogger(__name__)
console = cli_console.Console()

ASSET_INJECTION_AGENT_DEFAULT = "agent/ostorlab/inject_asset"
TRACKER_AGENT_DEFAULT = "agent/ostorlab/tracker"
LOCAL_PERSIST_VULNZ_AGENT_DEFAULT = "agent/ostorlab/local_persist_vulnz"

DEFAULT_AGENTS = [
    ASSET_INJECTION_AGENT_DEFAULT,
    TRACKER_AGENT_DEFAULT,
    LOCAL_PERSIST_VULNZ_AGENT_DEFAULT,
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
    return service.attrs["Spec"]["TaskTemplate"]["RestartPolicy"]["Condition"] == "none"


class LocalRuntime(runtime.Runtime):
    """Local runtime runs agents locally using Docker Swarm.
    Local runtime starts a Vanilla RabbitMQ service, starts all the agents listed in the `AgentRunDefinition`, checks
    their status and then inject the target asset.
    """

    def __init__(
        self,
        *args,
        scan_id: Optional[str] = None,
        tracing: Optional[bool] = False,
        mq_exposed_ports: Optional[Dict[int, int]] = None,
        gcp_logging_credential: Optional[str] = None,
        run_default_agents: bool = True,
        **kwargs,
    ) -> None:
        super().__init__()
        del args, kwargs
        self._scan_id = scan_id
        self.follow = []
        self._tracing = tracing
        self._mq_service: Optional[mq.LocalRabbitMQ] = None
        self._redis_service: Optional[redis.LocalRedis] = None
        self._jaeger_service: Optional[jaeger.LocalJaeger] = None
        self._log_streamer = log_streamer.LogStream()
        self._scan_db: Optional[models.Scan] = None
        self._mq_exposed_ports: Optional[Dict[int, int]] = mq_exposed_ports
        self._gcp_logging_credential = gcp_logging_credential
        self._run_default_agents: bool = run_default_agents

    @property
    def name(self) -> str:
        """Local runtime instance name."""
        if self._scan_id is not None:
            return self._scan_id
        elif self._scan_db is not None:
            return str(self._scan_db.id)
        else:
            raise ValueError("Scan not created yet")

    @property
    def network(self) -> str:
        """Local runtime network name.

        Returns:
            Local runtime network name.
        """
        return f"{NETWORK_PREFIX}_{self.name}"

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
        """checking the requirements (docker,swarm,arch,permissions) for ostorlab."""
        if not docker_requirements_checker.is_docker_installed():
            console.error("Docker is not installed.")
            raise click.exceptions.Exit(2)
        elif not docker_requirements_checker.is_sys_arch_supported():
            console.error("System architecture is not supported.")
            raise click.exceptions.Exit(2)
        elif not docker_requirements_checker.is_user_permitted():
            console.error("User does not have permissions to run docker.")
            raise click.exceptions.Exit(2)
        elif not docker_requirements_checker.is_docker_working():
            console.error("Error using docker.")
            raise click.exceptions.Exit(2)
        else:
            if not docker_requirements_checker.is_swarm_initialized():
                docker_requirements_checker.init_swarm()

        self._docker_client = docker.from_env()

    def scan(
        self,
        title: str,
        agent_group_definition: definitions.AgentGroupDefinition,
        assets: Optional[List[base_asset.Asset]],
    ) -> None:
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
            console.info("Creating scan entry")
            if assets is None:
                assets_str = "N/A"
            else:
                assets_str = f'{", ".join([str(asset) for asset in assets])}'
                # TODO(mohsinenar): we need to add support for storing multiple assets and rename this to target.
            self._scan_db = self._create_scan_db(asset=assets_str[:255], title=title)
            console.info("Creating network")
            self._create_network()
            console.info("Starting services")
            self._start_services()

            if self._run_default_agents is True:
                console.info("Starting pre-agents")
                self._start_pre_agents()

            console.info("Starting agents")
            self._start_agents(agent_group_definition)

            if self._run_default_agents is True:
                console.info("Starting post-agents")
                self._start_post_agents()

            console.info("Checking services are healthy")
            self._check_services_healthy()
            console.info("Checking agents are healthy")
            is_healthy = self._check_agents_healthy()
            if is_healthy is False:
                raise AgentNotHealthy()

            if assets is not None:
                self._inject_assets(assets)
            console.info("Updating scan status")
            self._update_scan_progress("IN_PROGRESS")
            console.success("Scan created successfully")
        except AgentNotHealthy:
            console.error("Agent not starting")
            self.stop(self._scan_db.id)
            self._update_scan_progress("ERROR")
            self.stop(str(self._scan_db.id))
        except AgentNotInstalled as e:
            console.error(f"Agent {e} not installed")
            self.stop(str(self._scan_db.id))
        except UnhealthyService as e:
            console.error(f"Unhealthy service {e}")
            self.stop(str(self._scan_db.id))
        except agent_runtime.MissingAgentDefinitionLabel as e:
            console.error(
                f"Missing agent definition {e}. This is probably due to building the image directly with"
                f" docker instead of `ostorlab agent build` command"
            )
            self.stop(str(self._scan_db.id))

    def stop(self, scan_id: str) -> None:
        """Remove a service (scan) belonging to universe with scan_id(Universe Id).

        Args:
            scan_id: The id of the scan to stop.
        """
        try:
            int_scan_id = int(scan_id)
        except ValueError as e:
            console.error("Scan id must be an integer.")
            raise click.exceptions.Exit(2) from e

        logger.info("stopping scan id %s", scan_id)
        stopped_services = []
        stopped_network = []
        stopped_configs = []
        self._docker_checks()
        services = self._docker_client.services.list()
        for service in services:
            service_labels = service.attrs["Spec"]["Labels"]
            logger.info(
                "comparing %s and %s", service_labels.get("ostorlab.universe"), scan_id
            )
            if service_labels.get("ostorlab.universe") == scan_id:
                stopped_services.append(service)
                service.remove()

        networks = self._docker_client.networks.list()
        for network in networks:
            network_labels = network.attrs["Labels"]
            if (
                network_labels is not None
                and network_labels.get("ostorlab.universe") == scan_id
            ):
                logger.info("removing network %s", network_labels)
                stopped_network.append(network)
                network.remove()

        configs = self._docker_client.configs.list()
        for config in configs:
            config_labels = config.attrs["Spec"]["Labels"]
            if config_labels.get("ostorlab.universe") == scan_id:
                logger.info("removing config %s", config_labels)
                stopped_configs.append(config)
                config.remove()

        if stopped_services or stopped_network or stopped_configs:
            console.success("All scan components stopped.")

        with models.Database() as session:
            scan = session.query(models.Scan).get(int_scan_id)
            if scan:
                scan.progress = "STOPPED"
                session.commit()
                console.success("Scan stopped successfully.")
            else:
                console.info(f"Scan {scan_id} was not found.")

    def _create_scan_db(self, title: str, asset: str):
        """Persist the scan in the database"""
        return models.Scan.create(title=title, asset=asset)

    def _update_scan_progress(self, progress: str):
        """Update scan status to in progress"""
        with models.Database() as session:
            scan = session.query(models.Scan).get(self._scan_db.id)
            scan.progress = progress
            session.commit()

    def _create_network(self):
        """Creates a docker swarm network where all services and agents can communicate."""
        if any(
            network.name == self.network
            for network in self._docker_client.networks.list()
        ):
            logger.warning("network already exists.")
        else:
            logger.info("creating private network %s", self.network)
            return self._docker_client.networks.create(
                name=self.network,
                driver="overlay",
                attachable=True,
                labels={"ostorlab.universe": self.name},
                check_duplicate=True,
            )

    def _start_services(self):
        """Start all the local runtime services."""
        self._start_mq_service()
        self._start_redis_service()
        if self._tracing is True:
            self._start_jaeger_service()

    def _start_mq_service(self):
        """Start a local rabbitmq service."""
        self._mq_service = mq.LocalRabbitMQ(
            name=self.name, network=self.network, exposed_ports=self._mq_exposed_ports
        )
        self._mq_service.start()
        if "mq" in self.follow:
            self._log_streamer.stream(self._mq_service.service)

    def _start_redis_service(self):
        """Start a local Redis service."""
        self._redis_service = redis.LocalRedis(name=self.name, network=self.network)
        self._redis_service.start()
        if "redis" in self.follow:
            self._log_streamer.stream(self._redis_service.service)

    def _start_jaeger_service(self):
        """Start a local Jaeger service."""
        self._jaeger_service = jaeger.LocalJaeger(name=self.name, network=self.network)
        self._jaeger_service.start()
        click.launch(self._jaeger_service.management_interface_ui)
        if "jaeger" in self.follow:
            self._log_streamer.stream(self._jaeger_service.service)

    def _check_services_healthy(self):
        """Check if the core services are running and healthy."""
        return self._are_services_ready()

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(20),
        wait=tenacity.wait_fixed(0.5),
        retry_error_callback=lambda lv: lv.outcome,
        retry=tenacity.retry_if_result(lambda v: v is False),
    )
    def _are_services_ready(self) -> bool:
        if self._mq_service is None or self._mq_service.is_service_healthy() is False:
            raise UnhealthyService("MQ service is unhealthy.")
        if (
            self._redis_service is None
            or self._redis_service.is_service_healthy() is False
        ):
            raise UnhealthyService("Redis service is unhealthy.")
        if self._tracing is True and (
            self._jaeger_service is None
            or self._jaeger_service.is_service_healthy() is False
        ):
            raise UnhealthyService("Jaeger service is unhealthy.")

    def _check_agents_healthy(self):
        """Checks if an agent is healthy."""
        return self._are_agents_ready()

    def _start_agents(self, agent_group_definition: definitions.AgentGroupDefinition):
        """Starts all the agents as list in the agent run definition."""
        with futures.ThreadPoolExecutor() as executor:
            future_to_agent = {
                executor.submit(self._start_agent, agent, extra_configs=[]): agent
                for agent in agent_group_definition.agents
            }
            for future in futures.as_completed(future_to_agent):
                future.result()

    def _start_pre_agents(self):
        """Starting pre-agents that must exist before other agents. This applies to all persistence
        agents that can start sending data at the start of the agent."""
        self._start_persist_vulnz_agent()

    def _start_post_agents(self):
        """Starting post-agents that must exist after other agents. This applies to the tracker
        that needs to monitor other agents."""
        self._start_tracker_agent()

    def _start_agent(
        self,
        agent: definitions.AgentSettings,
        extra_configs: Optional[List[docker.types.ConfigReference]] = None,
        extra_mounts: Optional[List[docker.types.Mount]] = None,
    ) -> None:
        """Start agent based on provided definition.

        Args:
            agent: An agent definition containing all the settings of how agent should run and what arguments to pass.
        """
        logger.info("starting agent %s with %s", agent.key, agent.args)

        if _has_container_image(agent) is False:
            raise AgentNotInstalled(agent.key)

        runtime_agent = agent_runtime.AgentRuntime(
            agent_settings=agent,
            runtime_name=self.name,
            docker_client=self._docker_client,
            mq_service=self._mq_service,
            redis_service=self._redis_service,
            jaeger_service=self._jaeger_service,
            gcp_logging_credential=self._gcp_logging_credential,
        )
        agent_service = runtime_agent.create_agent_service(
            network_name=self.network,
            extra_configs=extra_configs,
            extra_mounts=extra_mounts,
            replicas=agent.replicas or 1,
        )
        if agent.key in self.follow:
            self._log_streamer.stream(agent_service)

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(20),
        wait=tenacity.wait_fixed(0.5),
        # return last value and don't raise RetryError exception.
        retry_error_callback=lambda lv: lv.outcome,
        retry=tenacity.retry_if_result(lambda v: v is False),
    )
    def _is_service_healthy(
        self, service: docker_models_services.Service, replicas=None
    ) -> bool:
        """Checks if a docker service is healthy by checking all tasks status."""
        logger.debug("checking Spec service %s", service.name)
        try:
            if not replicas:
                replicas = service.attrs["Spec"]["Mode"]["Replicated"]["Replicas"]
            return replicas == len(
                [
                    task
                    for task in service.tasks()
                    if task["Status"]["State"] == "running"
                ]
            )
        except docker.errors.NotFound:
            return False

    def _list_agent_services(self):
        """List the services of type agents. All agent service must start with agent_."""
        services = self._docker_client.services.list(
            filters={"label": f"ostorlab.universe={self.name}"}
        )
        for service in services:
            if service.name.startswith("agent_"):
                yield service

    def _start_tracker_agent(self):
        """Start the tracker agent to handle the scan lifecycle."""
        tracker_agent_settings = definitions.AgentSettings(key=TRACKER_AGENT_DEFAULT)
        self._start_agent(agent=tracker_agent_settings, extra_configs=[])

    def _start_persist_vulnz_agent(self):
        """Start the local persistence agent to dump vulnerabilities in the local config."""
        persist_vulnz_agent_settings = definitions.AgentSettings(
            key=LOCAL_PERSIST_VULNZ_AGENT_DEFAULT, mounts=[]
        )
        self._start_agent(agent=persist_vulnz_agent_settings, extra_configs=[])

    def _inject_assets(self, assets: List[base_asset.Asset]):
        """Injects the scan target assets."""
        contents = {}
        for i, asset in enumerate(assets):
            console.info(f"Injecting asset: {asset}")
            contents[f"asset.binproto_{i}"] = asset.to_proto()
            contents[f"selector.txt_{i}"] = asset.selector.encode()

        volumes.create_volume(f"asset_{self.name}", contents)

        inject_asset_agent_settings = definitions.AgentSettings(
            key=ASSET_INJECTION_AGENT_DEFAULT, restart_policy="none"
        )
        self._start_agent(
            agent=inject_asset_agent_settings,
            extra_mounts=[
                docker.types.Mount(
                    target="/asset", source=f"asset_{self.name}", type="volume"
                )
            ],
        )

    def list(self, page: int = 1, number_elements: int = 10) -> List[runtime.Scan]:
        """Lists scans managed by runtime.

        Args:
            page: Page number for list pagination (default 1).
            number_elements: count of elements to show in the listed page (default 10).

        Returns:
            List of scan objects.
        """
        if page is not None:
            console.warning("Local runtime ignores scan list pagination")

        scans = {}
        with models.Database() as session:
            for scan in session.query(models.Scan):
                scans[scan.id] = runtime.Scan(
                    id=scan.id,
                    asset=scan.asset,
                    created_time=scan.created_time,
                    progress=scan.progress.value,
                )

        universe_ids = set()
        try:
            client = docker.from_env()
            services = client.services.list()
            for s in services:
                try:
                    service_labels = s.attrs["Spec"]["Labels"]
                    ostorlab_universe_id = service_labels.get("ostorlab.universe")
                    if (
                        "ostorlab.universe" in service_labels.keys()
                        and ostorlab_universe_id not in universe_ids
                    ):
                        universe_ids.add(ostorlab_universe_id)
                        if (
                            ostorlab_universe_id.isnumeric()
                            and int(ostorlab_universe_id) not in scans
                        ):
                            console.warning(
                                f"Scan {ostorlab_universe_id} has not traced in DB."
                            )
                except KeyError:
                    logger.warning("The label ostorlab.universe do not exist.")

            return list(scans.values())
        except docker_errors.DockerException as e:
            console.error(f"Error calling the Docker API: {e}")

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(20),
        wait=tenacity.wait_fixed(0.5),
        # return last value and don't raise RetryError exception.
        retry_error_callback=lambda lv: lv.outcome,
        retry=tenacity.retry_if_result(lambda v: v is False),
    )
    def _are_agents_ready(self, fail_fast=True) -> bool:
        """Checks that all agents are ready and healthy while taking into account the run type of agent
        (once vs long-running)."""
        logger.info("listing services ...")
        agent_services = list(self._list_agent_services())
        for service in agent_services:
            logger.info("checking %s ...", service.name)
            if not _is_service_type_run(service):
                if self._is_service_healthy(service):
                    logger.info("agent service %s is healthy", service.name)
                else:
                    logger.error("agent service %s is not healthy", service.name)
                    if fail_fast:
                        return False
        return True

    def install(self, docker_client: Optional[docker.DockerClient] = None) -> None:
        """Installs the default agents.

        Args:
            docker_client: optional instance of the docker client to use to install the agent.

        Returns:
            None
        """
        for agent_key in DEFAULT_AGENTS:
            try:
                install_agent.install(agent_key=agent_key, docker_client=docker_client)
            except agent_fetcher.AgentDetailsNotFound:
                console.warning(f"agent {agent_key} not found on the store")

    def list_vulnz(
        self,
        scan_id: int,
        filter_risk_rating: Optional[List[str]],
        search: Optional[str],
    ) -> None:
        try:
            with models.Database() as session:
                query = session.query(models.Vulnerability).filter_by(scan_id=scan_id)
                if filter_risk_rating is not None:
                    filter_risk_rating = [r.upper() for r in filter_risk_rating]
                    query = query.filter(
                        models.Vulnerability.risk_rating.in_(filter_risk_rating)
                    )

                if search is not None:
                    query = query.filter(
                        sqlalchemy.or_(
                            models.Vulnerability.title.ilike(f"%{search}%"),
                            models.Vulnerability.short_description.ilike(f"%{search}%"),
                            models.Vulnerability.description.ilike(f"%{search}%"),
                            models.Vulnerability.recommendation.ilike(f"%{search}%"),
                            models.Vulnerability.technical_detail.ilike(f"%{search}%"),
                        )
                    )

                vulnerabilities = query.order_by(models.Vulnerability.title).all()
            vulnz_list = []
            for vulnerability in vulnerabilities:
                vulnerability_location = vulnerability.location or ""
                vulnz_list.append(
                    {
                        "id": str(vulnerability.id),
                        "risk_rating": styles.style_risk(
                            vulnerability.risk_rating.value.upper()
                        ),
                        "cvss_v3_vector": vulnerability.cvss_v3_vector,
                        "title": vulnerability.title,
                        "short_description": markdown.Markdown(
                            vulnerability.short_description
                        ),
                        "location": markdown.Markdown(vulnerability_location),
                    }
                )

            columns = {
                "Id": "id",
                "Title": "title",
                "Vulnerable target": "location",
                "Risk rating": "risk_rating",
                "CVSS V3 Vector": "cvss_v3_vector",
                "Short Description": "short_description",
            }
            title = f"Scan {scan_id}: Found {len(vulnz_list)} vulnerabilities."
            console.table(columns=columns, data=vulnz_list, title=title)
            if len(vulnz_list) == 0:
                console.info("0 vulnerabilities were found.")
            else:
                console.success("Vulnerabilities listed successfully.")

        except sqlalchemy.exc.OperationalError:
            console.error(f"scan with id {scan_id} does not exist.")

    def _print_vulnerability(self, vulnerability):
        """Print vulnerability details"""
        if vulnerability is None:
            return

        vulnerability_location = vulnerability.location or ""
        vulnz_list = [
            {
                "id": str(vulnerability.id),
                "risk_rating": styles.style_risk(
                    vulnerability.risk_rating.value.upper()
                ),
                "cvss_v3_vector": vulnerability.cvss_v3_vector,
                "title": vulnerability.title,
                "short_description": markdown.Markdown(vulnerability.short_description),
                "location": markdown.Markdown(vulnerability_location),
            }
        ]
        columns = {
            "Id": "id",
            "Title": "title",
            "Vulnerable target": "location",
            "Risk rating": "risk_rating",
            "CVSS V3 Vector": "cvss_v3_vector",
            "Short Description": "short_description",
        }
        title = f"Describing vulnerability {vulnerability.id}"
        console.table(columns=columns, data=vulnz_list, title=title)
        rich.print(
            panel.Panel(
                markdown.Markdown(vulnerability.description), title="Description"
            )
        )
        rich.print(
            panel.Panel(
                markdown.Markdown(vulnerability.recommendation), title="Recommendation"
            )
        )
        if vulnerability.references is not None:
            rich.print(
                panel.Panel(
                    markdown.Markdown(vulnerability.references), title="References"
                )
            )
        rich.print(
            panel.Panel(
                markdown.Markdown(vulnerability.technical_detail),
                title="Technical details",
            )
        )

    def describe_vuln(self, scan_id: int, vuln_id: int):
        try:
            with models.Database() as session:
                vulnerabilities = []
                if vuln_id is not None:
                    vulnerability = session.query(models.Vulnerability).get(vuln_id)
                    vulnerabilities.append(vulnerability)
                elif scan_id is not None:
                    vulnerabilities = (
                        session.query(models.Vulnerability)
                        .filter_by(scan_id=scan_id)
                        .order_by(models.Vulnerability.title)
                        .all()
                    )
                for v in vulnerabilities:
                    self._print_vulnerability(v)
                console.success("Vulnerabilities listed successfully.")
        except sqlalchemy.exc.OperationalError:
            console.error("Vulnerability / scan not Found.")

    def dump_vulnz(self, scan_id: int, dumper: dumpers.VulnzDumper):
        """Dump found vulnerabilities of a scan in a specific format."""
        vulnerabilities = []
        with models.Database() as session:
            severity_sort_logic = case(
                value=models.Vulnerability.risk_rating, whens=risk_rating.RATINGS_ORDER
            ).label("severity")
            vulnerabilities = (
                session.query(models.Vulnerability)
                .filter_by(scan_id=scan_id)
                .order_by(severity_sort_logic)
                .all()
            )
        vulnz_list = []
        for vulnerability in vulnerabilities:
            vuln = {
                "id": vulnerability.id,
                "risk_rating": vulnerability.risk_rating.value,
                "cvss_v3_vector": vulnerability.cvss_v3_vector,
                "title": vulnerability.title,
                "short_description": vulnerability.short_description,
                "description": vulnerability.description,
                "recommendation": vulnerability.recommendation,
                "references": vulnerability.references,
                "technical_detail": vulnerability.technical_detail,
                "location": vulnerability.location,
            }
            vulnz_list.append(vuln)
        dumper.dump(vulnz_list)
        console.success(
            f"{len(vulnerabilities)} Vulnerabilities saved to  : {dumper.output_path}"
        )
