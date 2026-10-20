"""Local runtime runs agents locally.

The local runtime requires Docker Swarm to run robust long-running services with a set of configured services, like
a local RabbitMQ.
"""

from __future__ import annotations

import builtins
import logging
import threading
import typing
from concurrent import futures
from urllib import parse

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
from sqlalchemy import orm

from ostorlab import exceptions
from ostorlab.assets import asset as base_asset
from ostorlab.cli import agent_fetcher
from ostorlab.cli import console as cli_console
from ostorlab.cli import docker_requirements_checker
from ostorlab.cli import dumpers
from ostorlab.cli import install_agent
from ostorlab.runtimes import definitions
from ostorlab.runtimes import docker_cleanup
from ostorlab.runtimes import runtime
from ostorlab.runtimes.local import agent_runtime
from ostorlab.runtimes.local import log_streamer
from ostorlab.runtimes.local import scan_state
from ostorlab.runtimes.local import snapshot
from ostorlab.runtimes.local.models import models
from ostorlab.runtimes.local.services import container_exec
from ostorlab.runtimes.local.services import jaeger
from ostorlab.runtimes.local.services import mq
from ostorlab.runtimes.local.services import redis
from ostorlab.utils import definitions as utils_definitions
from ostorlab.utils import risk_rating
from ostorlab.utils import styles
from ostorlab.utils import volumes

NETWORK_PREFIX = "ostorlab_local_network"

logger = logging.getLogger(__name__)
console = cli_console.Console(logger=logger)

ASSET_CLOUD_INJECTION_AGENT = "agent/ostorlab/cloud_inject_asset"
ASSET_INJECTION_AGENT_DEFAULT = "agent/ostorlab/inject_asset"
TRACKER_AGENT_DEFAULT = "agent/ostorlab/tracker"
LOCAL_PERSIST_VULNZ_AGENT_DEFAULT = "agent/ostorlab/local_persist_vulnz"

# Time given to the containers of the removed services of a paused scan to exit.
SERVICES_STOP_ATTEMPTS = 60
SERVICES_STOP_WAIT_SECONDS = 1

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


class MissingAgentDefinition(exceptions.OstorlabError):
    """Agent definition is missing."""


class SnapshotRestoreError(exceptions.OstorlabError):
    """The paused scan could not be restored from its snapshot."""


class ScanPauseError(exceptions.OstorlabError):
    """The scan could not be paused."""


class ScanResumeError(exceptions.OstorlabError):
    """The scan could not be resumed."""


class ServicesNotStopped(exceptions.OstorlabError):
    """The containers of the removed services are still running."""


def _has_container_image(agent: definitions.AgentSettings) -> bool:
    """Check if container image is available"""
    return agent.container_image is not None


def _is_service_type_run(service: docker_models_services.Service) -> bool:
    """Checks if the service should run once or should be continuously running.

    Args:
        service: Docker service.

    Returns:
        Bool indicating if the service is run-once or long-running.
    """
    return (
        typing.cast(
            str, service.attrs["Spec"]["TaskTemplate"]["RestartPolicy"]["Condition"]
        )
        == "none"
    )


class LocalRuntime(runtime.Runtime[int | str]):
    """Local runtime runs agents locally using Docker Swarm.
    Local runtime starts a Vanilla RabbitMQ service, starts all the agents listed in the `AgentRunDefinition`, checks
    their status and then inject the target asset.
    """

    def __init__(
        self,
        *args: object,
        scan_id: typing.Optional[int | str] = None,
        labels: typing.Optional[dict[str, str]] = None,
        tracing: typing.Optional[bool] = False,
        mq_exposed_ports: typing.Optional[dict[int, int]] = None,
        gcp_logging_credential: typing.Optional[str] = None,
        run_default_agents: bool = True,
        snapshot_settings: typing.Optional[definitions.SnapshotSettings] = None,
        **kwargs: object,
    ) -> None:
        super().__init__()
        del args, kwargs
        self._scan_id = scan_id
        self._labels = labels if labels is not None else {}
        self.follow = []
        self._tracing = tracing
        self._mq_service: typing.Optional[mq.LocalRabbitMQ] = None
        self._redis_service: typing.Optional[redis.LocalRedis] = None
        self._jaeger_service: typing.Optional[jaeger.LocalJaeger] = None
        self._scan_db: typing.Optional[models.Scan] = None
        self._mq_exposed_ports: typing.Optional[dict[int, int]] = mq_exposed_ports
        self._gcp_logging_credential = gcp_logging_credential
        self._run_default_agents: bool = run_default_agents
        self._snapshot_settings = snapshot_settings
        # Snapshot of the scan resumed with `resume`, restored instead of the one of the snapshot storage.
        self._paused_snapshot: typing.Optional[snapshot.UniverseSnapshot] = None
        self._log_streamer: typing.Optional[log_streamer.LogStream] = None
        self._docker_client: typing.Optional[docker.DockerClient] = None

    @property
    def name(self) -> int | str:
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

    def _docker_checks(self) -> None:
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

        self._docker_client = docker.from_env(max_pool_size=100)

    def prepare_scan(self, title: typing.Optional[str]) -> models.Scan:
        """Prepare scan entry in the database.

        Args:
            title: Scan title.
        """
        self._scan_db = self._create_scan_db(title=title)
        return self._scan_db

    def _handle_scan_error(self) -> None:
        """Update scan progress to ERROR and trigger cleanup gracefully."""
        try:
            self._update_scan_progress(models.ScanProgress.ERROR)
        except (
            sqlalchemy.exc.SQLAlchemyError,
            exceptions.OstorlabError,
            AttributeError,
            ValueError,
        ) as update_err:
            logger.warning("Failed to update scan progress to ERROR: %s", update_err)
        try:
            self.cleanup()
        except (
            docker_errors.DockerException,
            docker_errors.APIError,
            click.exceptions.Exit,
            exceptions.OstorlabError,
            ValueError,
        ) as cleanup_err:
            logger.warning(
                "Failed to clean up scan resources after error: %s", cleanup_err
            )

    def scan(
        self,
        title: typing.Optional[str],
        agent_group_definition: definitions.AgentGroupDefinition,
        assets: typing.Optional[typing.Sequence[base_asset.Asset]],
    ) -> typing.Optional[models.Scan]:
        """Start scan on asset using the provided agent run definition.

        The scan takes care of starting all the scan required services, ensuring they are healthy, starting all the
         agents, ensuring they are healthy and then injects the target asset.

        Args:
            title: Scan title
            agent_group_definition: Agent run definition defines the set of agents and how agents are configured.
            assets: the target asset to scan.

        Returns:
            The scan object.
        """
        self._log_streamer = log_streamer.LogStream(
            typing.cast(docker.DockerClient, self._docker_client)
        )
        try:
            if self._scan_db is None:
                self.prepare_scan(title=title)
            console.info("Creating network")
            self._create_network()
            console.info("Starting services")
            self._start_services()
            console.info("Checking services are healthy")
            self._check_services_healthy()

            universe_snapshot = self._load_snapshot()
            if universe_snapshot is not None:
                console.info("Restoring the paused scan")
                self._restore_snapshot(universe_snapshot)
                # The restored queues hold the messages of the scan, the assets were injected when it started.
                assets = None

            if self._run_default_agents is True:
                console.info("Starting pre-agents")
                self._start_pre_agents()

            console.info("Starting agents")
            self._start_agents(agent_group_definition)

            if self._run_default_agents is True:
                console.info("Starting post-agents")
                self._start_post_agents()

            console.info("Checking agents are healthy")
            is_healthy = self._check_agents_healthy()
            if is_healthy is False:
                raise AgentNotHealthy()

            if assets is not None:
                inject_asset_agent_settings = next(
                    (
                        agent
                        for agent in agent_group_definition.agents
                        if agent.key == ASSET_CLOUD_INJECTION_AGENT
                    ),
                    None,
                )
                console.info("Injecting assets")
                self._inject_assets(
                    assets=assets,
                    agent_settings=inject_asset_agent_settings,
                )
            if self._scan_id is None:
                # Saved once the scan started: a scan failing to start cannot be paused, it needs no definition.
                self._save_scan_definition(agent_group_definition)
            console.info("Updating scan status")
            self._update_scan_progress(models.ScanProgress.IN_PROGRESS)
            console.success("Scan created successfully")

            self._wait_log_streamer()

            return self._scan_db
        except AgentNotHealthy:
            message = "Agent not starting"
            self._handle_scan_error()
            raise AgentNotHealthy(message)
        except AgentNotInstalled as e:
            message = f"Agent {e} not installed"
            self._handle_scan_error()
            raise AgentNotInstalled(message)
        except UnhealthyService as e:
            message = f"Unhealthy service {e}"
            self._handle_scan_error()
            raise UnhealthyService(message)
        except agent_runtime.MissingAgentDefinitionLabel as e:
            message = (
                f"Missing agent definition {e}. This is probably due to building the image directly with"
                f" docker instead of `oxo agent build` command"
            )
            self._handle_scan_error()
            raise MissingAgentDefinition(message)
        except (Exception, KeyboardInterrupt) as e:
            logger.error("Unhandled error during scan execution: %s", e)
            self._handle_scan_error()
            raise

    def _load_snapshot(self) -> typing.Optional[snapshot.UniverseSnapshot]:
        """Snapshot of the scan when it was paused, None for a scan that was never paused.

        A scan paused with `oxo scan pause` gets the snapshot read by `resume`, the others the one of the snapshot
        storage.

        Raises:
            snapshot.StorageError: When the snapshot bucket cannot be read.
            SnapshotRestoreError: When the snapshot of the scan is not a valid snapshot.
        """
        if self._paused_snapshot is not None:
            return self._paused_snapshot
        if self._snapshot_settings is None:
            return None
        try:
            return snapshot.load(
                self._snapshot_settings, snapshot.object_name(self.name)
            )
        except snapshot.InvalidSnapshotError as e:
            raise SnapshotRestoreError(
                f"could not read the snapshot of scan {self.name}: {e}"
            ) from e

    def _restore_snapshot(self, universe_snapshot: snapshot.UniverseSnapshot) -> None:
        """Restore the MQ and Redis state of a paused scan, once the services are ready and before the agents start.

        Raises:
            SnapshotRestoreError: When the snapshot cannot be restored.
        """
        try:
            typing.cast(redis.LocalRedis, self._redis_service).restore(
                universe_snapshot.redis_keys
            )
            typing.cast(mq.LocalRabbitMQ, self._mq_service).restore(
                exchanges=universe_snapshot.exchanges, queues=universe_snapshot.queues
            )
        except container_exec.ExecError as e:
            raise SnapshotRestoreError(
                f"could not restore the snapshot of scan {self.name}: {e}"
            ) from e

    def _wait_log_streamer(self) -> None:
        """Spawns a (Non-daemon) thread that blocks until all the log steams finish."""
        threading.Thread(
            target=typing.cast(log_streamer.LogStream, self._log_streamer).wait,
            daemon=False,
        ).start()

    def cleanup(self, scan_id: typing.Optional[int | str] = None) -> bool:
        """Remove all Docker services, networks, configs, and volumes belonging to universe with scan_id (Universe Id).

        Args:
            scan_id: The id of the scan to stop. If None, defaults to the runtime's scan identifier.

        Returns:
            bool: True if cleanup completed without error, False otherwise.
        """
        if scan_id is None:
            scan_id = (
                self._scan_id
                if self._scan_id is not None
                else (self._scan_db.id if self._scan_db is not None else None)
            )

        if scan_id is None:
            logger.warning("No valid scan_id provided to cleanup.")
            return True

        if self._docker_client is None:
            try:
                self._docker_checks()
            except (
                docker.errors.DockerException,
                click.exceptions.Exit,
                exceptions.OstorlabError,
            ) as e:
                logger.warning("Docker checks failed during cleanup: %s", e)
                return False

        return docker_cleanup.cleanup_scan_docker_resources(
            typing.cast(docker.DockerClient, self._docker_client), scan_id
        )

    def stop(
        self,
        scan_id: typing.Optional[int | str] = None,
        update_scan_status: bool = True,
    ) -> None:
        """Remove all services, networks, configs, and volumes belonging to universe with scan_id (Universe Id).

        Args:
            scan_id: The id of the scan to stop. If None, defaults to the runtime's scan identifier.
            update_scan_status: Whether to update the scan progress to STOPPED in the local database.
        """
        if scan_id is None:
            scan_id = (
                self._scan_id
                if self._scan_id is not None
                else (self._scan_db.id if self._scan_db is not None else None)
            )

        if scan_id is None:
            logger.warning("No valid scan_id provided to stop.")
            return

        cleanup_success = self.cleanup(scan_id=scan_id)

        if update_scan_status is True and cleanup_success is True:
            target_db_id = None
            if self._scan_db is not None and (
                scan_id is None or scan_id == self._scan_db.id
            ):
                target_db_id = self._scan_db.id
            elif isinstance(scan_id, int):
                target_db_id = scan_id

            if target_db_id is not None:
                with models.Database() as session:
                    scan = typing.cast(
                        "orm.Query[models.Scan]", session.query(models.Scan)
                    ).get(target_db_id)
                    if scan is not None:
                        scan.progress = models.ScanProgress.STOPPED
                        session.commit()
                        # A stopped scan cannot be resumed, its definition and snapshot are not needed anymore.
                        scan_state.delete(target_db_id)
                        console.success("Scan stopped successfully.")
                    else:
                        console.info(f"Scan {target_db_id} was not found.")
        elif update_scan_status is True and cleanup_success is False:
            logger.warning(
                "Cleanup had errors for scan %s; not updating scan progress to STOPPED.",
                scan_id,
            )

    def pause(self, scan_id: int) -> None:
        """Pause a running scan: stop its agents, keep its MQ and Redis state in a local snapshot and remove its universe.

        The agents are stopped first: the messages they did not acknowledge go back to their queues and are in the
        snapshot. `resume` starts the scan again from the snapshot.

        Args:
            scan_id: Id of the scan in the local database.

        Raises:
            ScanPauseError: When the scan cannot be paused. A scan whose agents were stopped but whose snapshot could
                not be taken is stopped.
        """
        self._docker_checks()
        scan_db = self._get_scan_db(scan_id)
        if scan_db is None:
            raise ScanPauseError(f"scan {scan_id} was not found.")
        if scan_db.progress != models.ScanProgress.IN_PROGRESS:
            raise ScanPauseError(f"scan {scan_id} is not running.")
        self._scan_db = scan_db
        try:
            if scan_state.load_definition(scan_id) is None:
                raise ScanPauseError(
                    f"scan {scan_id} was started by an oxo version that cannot resume it."
                )
        except scan_state.Error as e:
            raise ScanPauseError(
                f"could not read the definition of scan {scan_id}: {e}"
            ) from e
        mq_service = mq.LocalRabbitMQ(name=self.name, network=self.network)
        try:
            has_mq_service = mq_service.attach()
        except docker_errors.DockerException as e:
            raise ScanPauseError(
                f"could not find the MQ service of scan {scan_id}: {e}"
            ) from e
        if has_mq_service is False:
            raise ScanPauseError(f"scan {scan_id} has no running MQ service.")

        console.info("Stopping the agents")
        try:
            self._stop_agents()
            console.info("Taking the snapshot of the scan")
            redis_host = parse.urlparse(
                redis.LocalRedis(name=self.name, network=self.network).url
            ).hostname
            universe_snapshot = snapshot.from_document(
                mq_service.capture(redis_host=typing.cast(str, redis_host))
            )
            snapshot.save_file(scan_state.snapshot_path(scan_id), universe_snapshot)
        except (
            ServicesNotStopped,
            container_exec.ExecError,
            snapshot.Error,
            docker_errors.DockerException,
        ) as e:
            # The agents may be stopped, the scan cannot go on without its snapshot: it is stopped even when some of
            # its resources cannot be removed.
            if self.cleanup(scan_id=scan_id) is False:
                logger.warning("could not remove every resource of scan %s", scan_id)
            self._update_scan_progress(models.ScanProgress.STOPPED)
            scan_state.delete(scan_id)
            raise ScanPauseError(
                f"could not take the snapshot of scan {scan_id}, the scan was stopped: {e}"
            ) from e

        console.info("Removing the services of the scan")
        # The MQ data volume is removed once its container exited, a resumed MQ must not reload the paused messages
        # the snapshot restores. A resource left here is removed when the scan resumes.
        try:
            self._stop_services()
        except (ServicesNotStopped, docker_errors.DockerException) as e:
            logger.warning("could not stop the services of scan %s: %s", scan_id, e)
        self.cleanup(scan_id=scan_id)
        self._update_scan_progress(models.ScanProgress.PAUSED)
        console.success("Scan paused successfully.")

    def resume(self, scan_id: int) -> typing.Optional[models.Scan]:
        """Resume a paused scan: start its services, restore its snapshot, then start its agents again.

        Args:
            scan_id: Id of the scan in the local database.

        Returns:
            The scan object.

        Raises:
            ScanResumeError: When the scan is not paused or its state cannot be read.
        """
        self._docker_checks()
        scan_db = self._get_scan_db(scan_id)
        if scan_db is None:
            raise ScanResumeError(f"scan {scan_id} was not found.")
        if scan_db.progress != models.ScanProgress.PAUSED:
            raise ScanResumeError(f"scan {scan_id} is not paused.")
        try:
            scan_definition = scan_state.load_definition(scan_id)
            universe_snapshot = snapshot.load_file(scan_state.snapshot_path(scan_id))
        except (scan_state.Error, snapshot.Error) as e:
            raise ScanResumeError(
                f"could not read the state of scan {scan_id}: {e}"
            ) from e
        if scan_definition is None or universe_snapshot is None:
            raise ScanResumeError(f"scan {scan_id} has no snapshot to resume from.")

        # Resources left by the pause, like a MQ data volume that could not be removed, would duplicate the restored
        # messages.
        if self.cleanup(scan_id=scan_id) is False:
            raise ScanResumeError(
                f"could not remove the resources left by the pause of scan {scan_id}."
            )
        self._scan_db = scan_db
        self._paused_snapshot = universe_snapshot
        self.has_tracker = scan_definition.has_tracker
        self.timeout = scan_definition.timeout
        self.init_sleep = scan_definition.init_sleep
        self.follow = scan_definition.follow
        try:
            resumed_scan = self.scan(
                title=scan_db.title,
                agent_group_definition=scan_definition.agent_group_definition,
                assets=None,
            )
        except (Exception, KeyboardInterrupt):
            # The failed start marked the scan as an error and removed its universe, the scan keeps its snapshot to be
            # resumed again.
            self._update_scan_progress(models.ScanProgress.PAUSED)
            raise
        scan_state.delete_snapshot(scan_id)
        return resumed_scan

    def _get_scan_db(self, scan_id: int) -> typing.Optional[models.Scan]:
        with models.Database() as session:
            return typing.cast(
                "orm.Query[models.Scan]", session.query(models.Scan)
            ).get(scan_id)

    def _save_scan_definition(
        self, agent_group_definition: definitions.AgentGroupDefinition
    ) -> None:
        """Store what is needed to start the agents of the scan again, read by `resume` from another oxo process."""
        try:
            scan_state.save_definition(
                self.name,
                scan_state.ScanDefinition(
                    agent_group_definition=agent_group_definition,
                    has_tracker=self.has_tracker,
                    timeout=self.timeout,
                    init_sleep=self.init_sleep,
                    follow=builtins.list(self.follow),
                ),
            )
        except scan_state.Error as e:
            # The scan runs without its definition, it only cannot be paused.
            logger.warning("%s", e)

    def _stop_agents(self) -> None:
        """Remove the agent services of the scan and wait for their containers to exit, the MQ and Redis keep
        running.

        Every agent service has the `ostorlab.queue_name` label, its name may not start with `agent_` when its
        definition sets a service name.
        """
        self._remove_services(
            typing.cast(docker.DockerClient, self._docker_client).services.list(
                filters={
                    "label": [f"ostorlab.universe={self.name}", "ostorlab.queue_name"]
                }
            )
        )

    def _stop_services(self) -> None:
        """Remove the remaining services of the scan, like the MQ and Redis, and wait for their containers to exit."""
        self._remove_services(
            typing.cast(docker.DockerClient, self._docker_client).services.list(
                filters={"label": f"ostorlab.universe={self.name}"}
            )
        )

    def _remove_services(
        self, services: builtins.list[docker_models_services.Service]
    ) -> None:
        for service in services:
            logger.info("stopping service %s", service.name)
            typing.cast(typing.Callable[[], None], service.remove)()
        self._wait_services_stopped([service.name for service in services])

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(SERVICES_STOP_ATTEMPTS),
        wait=tenacity.wait_fixed(SERVICES_STOP_WAIT_SECONDS),
        retry=tenacity.retry_if_exception_type(ServicesNotStopped),
        reraise=True,
    )
    def _wait_services_stopped(self, service_names: builtins.list[str]) -> None:
        docker_client = typing.cast(docker.DockerClient, self._docker_client)
        for service_name in service_names:
            containers = docker_client.containers.list(
                # An exited container keeps its volumes until swarm removes it.
                all=True,
                filters={"label": f"com.docker.swarm.service.name={service_name}"},
            )
            if len(containers) > 0:
                raise ServicesNotStopped(f"service {service_name} is still running.")

    def _create_scan_db(self, title: typing.Optional[str]) -> models.Scan:
        """Persist the scan in the database"""
        return models.Scan.create(title=title)

    def _update_scan_progress(self, progress: models.ScanProgress) -> None:
        """Update scan status to in progress"""
        if self._scan_db is None:
            return
        with models.Database() as session:
            scan = typing.cast(
                "orm.Query[models.Scan]", session.query(models.Scan)
            ).get(self._scan_db.id)
            if scan is not None:
                scan.progress = progress
                session.commit()

    def _create_network(self) -> typing.Optional[docker.models.networks.Network]:
        """Creates a docker swarm network where all services and agents can communicate."""
        if any(
            network.name == self.network
            for network in typing.cast(
                docker.DockerClient, self._docker_client
            ).networks.list()
        ):
            logger.warning("network already exists.")
        else:
            logger.info("creating private network %s", self.network)
            return typing.cast(
                docker.DockerClient, self._docker_client
            ).networks.create(
                name=self.network,
                driver="overlay",
                attachable=True,
                labels={"ostorlab.universe": self.name},
                check_duplicate=True,
            )
        return None

    def _start_services(self) -> None:
        """Start all the local runtime services."""
        self._start_mq_service()
        self._start_redis_service()
        if self._tracing is True:
            self._start_jaeger_service()

    def _start_mq_service(self) -> None:
        """Start a local rabbitmq service."""
        self._mq_service = mq.LocalRabbitMQ(
            name=self.name, network=self.network, exposed_ports=self._mq_exposed_ports
        )
        self._mq_service.start()
        if "mq" in self.follow:
            typing.cast(log_streamer.LogStream, self._log_streamer).stream(
                typing.cast(docker_models_services.Service, self._mq_service.service)
            )

    def _start_redis_service(self) -> None:
        """Start a local Redis service."""
        self._redis_service = redis.LocalRedis(name=self.name, network=self.network)
        self._redis_service.start()
        if "redis" in self.follow:
            typing.cast(log_streamer.LogStream, self._log_streamer).stream(
                typing.cast(docker_models_services.Service, self._redis_service.service)
            )

    def _start_jaeger_service(self) -> None:
        """Start a local Jaeger service."""
        self._jaeger_service = jaeger.LocalJaeger(name=self.name, network=self.network)
        self._jaeger_service.start()
        click.launch(self._jaeger_service.management_interface_ui)
        if "jaeger" in self.follow:
            typing.cast(log_streamer.LogStream, self._log_streamer).stream(
                typing.cast(
                    docker_models_services.Service, self._jaeger_service.service
                )
            )

    def _check_services_healthy(self) -> None:
        """Check if the core services are running and healthy."""
        return self._are_services_ready()

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(20),
        wait=tenacity.wait_fixed(0.5),
        retry_error_callback=lambda lv: lv.outcome,
        retry=tenacity.retry_if_result(lambda v: v is False),
    )
    def _are_services_ready(self) -> None:
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

    def _check_agents_healthy(self) -> bool | tenacity.Future:
        """Checks if an agent is healthy."""
        return self._are_agents_ready()

    def _start_agents(
        self, agent_group_definition: definitions.AgentGroupDefinition
    ) -> None:
        """Starts all the agents as list in the agent run definition."""
        with futures.ThreadPoolExecutor() as executor:
            future_to_agent = {
                executor.submit(self._start_agent, agent, extra_configs=[]): agent
                for agent in agent_group_definition.agents
                if agent.key != ASSET_CLOUD_INJECTION_AGENT
            }
            for future in futures.as_completed(future_to_agent):
                future.result()

    def _start_pre_agents(self) -> None:
        """Starting pre-agents that must exist before other agents. This applies to all persistence
        agents that can start sending data at the start of the agent."""
        self._start_persist_vulnz_agent()

    def _start_post_agents(self) -> None:
        """Starting post-agents that must exist after other agents. This applies to the tracker
        that needs to monitor other agents."""
        self._start_tracker_agent()

    def _start_agent(
        self,
        agent: definitions.AgentSettings,
        extra_configs: typing.Optional[list[docker.types.ConfigReference]] = None,
        extra_mounts: typing.Optional[list[docker.types.Mount]] = None,
    ) -> None:
        """Start agent based on provided definition.

        Args:
            agent: An agent definition containing all the settings of how agent should run and what arguments to pass.
        """
        logger.info("starting agent %s", agent.key)

        if _has_container_image(agent) is False:
            raise AgentNotInstalled(agent.key)

        # The snapshot storage is shared by the scan like the bus and redis, every agent receives the runtime's one.
        agent.snapshot = self._snapshot_settings

        runtime_agent = agent_runtime.AgentRuntime(
            agent_settings=agent,
            runtime_name=self.name,
            docker_client=typing.cast(docker.DockerClient, self._docker_client),
            mq_service=self._mq_service,
            redis_service=self._redis_service,
            jaeger_service=self._jaeger_service,
            gcp_logging_credential=self._gcp_logging_credential,
            labels=self._labels,
        )
        agent_service = runtime_agent.create_agent_service(
            network_name=self.network,
            extra_configs=extra_configs,
            extra_mounts=extra_mounts,
            replicas=agent.replicas or 1,
        )
        if agent.key in self.follow:
            typing.cast(log_streamer.LogStream, self._log_streamer).stream(
                agent_service
            )

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(20),
        wait=tenacity.wait_fixed(0.5),
        # return last value and don't raise RetryError exception.
        retry_error_callback=lambda lv: lv.outcome,
        retry=tenacity.retry_if_result(lambda v: v is False),
    )
    def _is_service_healthy(
        self,
        service: docker_models_services.Service,
        replicas: typing.Optional[int] = None,
    ) -> bool | tenacity.Future:
        """Checks if a docker service is healthy by checking all tasks status."""
        logger.debug("checking Spec service %s", service.name)
        try:
            if not replicas:
                replicas = typing.cast(
                    int, service.attrs["Spec"]["Mode"]["Replicated"]["Replicas"]
                )
            return replicas == len(
                [
                    task
                    for task in typing.cast(
                        typing.Callable[[], list[dict[str, typing.Any]]], service.tasks
                    )()
                    if task["Status"]["State"] == "running"
                ]
            )
        except docker.errors.NotFound:
            return False

    def _list_agent_services(self) -> typing.Iterator[docker_models_services.Service]:
        """List the services of type agents. All agent service must start with agent_."""
        services = typing.cast(docker.DockerClient, self._docker_client).services.list(
            filters={"label": f"ostorlab.universe={self.name}"}
        )
        for service in services:
            if service.name.startswith("agent_"):
                yield service

    def _start_tracker_agent(self) -> None:
        """Start the tracker agent to handle the scan lifecycle."""
        if self.has_tracker is False:
            return

        tracker_agent_settings = definitions.AgentSettings(
            key=TRACKER_AGENT_DEFAULT,
        )
        if self.timeout is not None:
            tracker_agent_settings.args.extend(
                [
                    utils_definitions.Arg(
                        name="scan_done_timeout_sec", type="number", value=self.timeout
                    ),
                ]
            )
        if self.init_sleep is not None:
            tracker_agent_settings.args.extend(
                [
                    utils_definitions.Arg(
                        name="init_sleep_seconds", type="number", value=self.init_sleep
                    ),
                ]
            )
        self._start_agent(agent=tracker_agent_settings, extra_configs=[])

    def _start_persist_vulnz_agent(self) -> None:
        """Start the local persistence agent to dump vulnerabilities in the local config."""
        persist_vulnz_agent_settings = definitions.AgentSettings(
            key=LOCAL_PERSIST_VULNZ_AGENT_DEFAULT, mounts=[]
        )
        self._start_agent(agent=persist_vulnz_agent_settings, extra_configs=[])

    def _inject_assets(
        self,
        assets: typing.Sequence[base_asset.Asset],
        agent_settings: typing.Optional[definitions.AgentSettings],
    ) -> None:
        """Injects the scan target assets."""
        contents = {}
        for i, asset in enumerate(assets):
            console.info(f"Injecting asset: {asset}")
            contents[f"asset.binproto_{i}"] = asset.to_proto()
            contents[f"selector.txt_{i}"] = asset.selector.encode()

        volumes.create_volume(
            f"asset_{self.name}",
            contents,
            labels=typing.cast(dict[str, str], {"ostorlab.universe": self.name}),
        )

        if agent_settings is None:
            agent_settings = definitions.AgentSettings(
                key=ASSET_INJECTION_AGENT_DEFAULT, restart_policy="none"
            )

        self._start_agent(
            agent=agent_settings,
            extra_mounts=[
                docker.types.Mount(
                    target="/asset", source=f"asset_{self.name}", type="volume"
                )
            ],
        )

    def list(
        self,
        page: int = 1,
        number_elements: int = 10,
        state: typing.Optional[str] = None,
    ) -> typing.Optional[list[runtime.Scan]]:
        """Lists scans managed by runtime.

        Args:
            page: Page number for list pagination (default 1).
            number_elements: count of elements to show in the listed page (default 10).
            state: Filter scans by state.

        Returns:
            List of scan objects.
        """
        if page is not None:
            console.warning("Local runtime ignores scan list pagination")

        scans = {}
        with models.Database() as session:
            query = typing.cast("orm.Query[models.Scan]", session.query(models.Scan))
            if state is not None:
                query = query.filter(models.Scan.progress == models.ScanProgress(state))
            for scan in query:
                scans[scan.id] = runtime.Scan(
                    id=scan.id,
                    created_time=scan.created_time,
                    progress=typing.cast(models.ScanProgress, scan.progress).value,
                    risk_rating=scan.risk_rating,
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
                        "ostorlab.universe" in service_labels
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
            return None

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(20),
        wait=tenacity.wait_fixed(0.5),
        # return last value and don't raise RetryError exception.
        retry_error_callback=lambda lv: lv.outcome,
        retry=tenacity.retry_if_result(lambda v: v is False),
    )
    def _are_agents_ready(self, fail_fast: bool = True) -> bool | tenacity.Future:
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

    def install(
        self, docker_client: typing.Optional[docker.DockerClient] = None
    ) -> None:
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
        filter_risk_rating: typing.Optional[builtins.list[str]] = None,
        search: typing.Optional[str] = None,
        order_by: str = "risk_rating",
    ) -> None:
        try:
            with models.Database() as session:
                query = typing.cast(
                    "orm.Query[models.Vulnerability]",
                    session.query(models.Vulnerability),
                ).filter_by(scan_id=scan_id)
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

                if order_by == "risk_rating":
                    case_ordering: sqlalchemy.sql.elements.Case[sqlalchemy.Integer] = (
                        case(
                            [
                                (models.Vulnerability.risk_rating == rating, order)
                                for rating, order in risk_rating.RATINGS_ORDER.items()
                            ],
                            else_=len(risk_rating.RATINGS_ORDER),
                        )
                    )
                    vulnerabilities = query.order_by(
                        case_ordering, models.Vulnerability.title
                    ).all()
                elif order_by == "title":
                    vulnerabilities = query.order_by(models.Vulnerability.title).all()
                elif order_by == "id":
                    vulnerabilities = query.order_by(models.Vulnerability.id).all()

            vulnz_list = []
            for vulnerability in vulnerabilities:
                vulnerability_location = vulnerability.location or ""
                vulnz_list.append(
                    {
                        "id": str(vulnerability.id),
                        "risk_rating": styles.style_risk(
                            typing.cast(
                                risk_rating.RiskRating, vulnerability.risk_rating
                            ).value.upper()
                        ),
                        "cvss_v3_vector": vulnerability.cvss_v3_vector,
                        "title": vulnerability.title,
                        "short_description": markdown.Markdown(
                            typing.cast(str, vulnerability.short_description)
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

    def _print_vulnerability(
        self, vulnerability: typing.Optional[models.Vulnerability]
    ) -> None:
        """Print vulnerability details"""
        if vulnerability is None:
            return

        vulnerability_location = vulnerability.location or ""
        vulnz_list = [
            {
                "id": str(vulnerability.id),
                "risk_rating": styles.style_risk(
                    typing.cast(
                        risk_rating.RiskRating, vulnerability.risk_rating
                    ).value.upper()
                ),
                "cvss_v3_vector": vulnerability.cvss_v3_vector,
                "title": vulnerability.title,
                "short_description": markdown.Markdown(
                    typing.cast(str, vulnerability.short_description)
                ),
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
                markdown.Markdown(typing.cast(str, vulnerability.description)),
                title="Description",
            )
        )
        rich.print(
            panel.Panel(
                markdown.Markdown(typing.cast(str, vulnerability.recommendation)),
                title="Recommendation",
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
                markdown.Markdown(typing.cast(str, vulnerability.technical_detail)),
                title="Technical details",
            )
        )
        if vulnerability.exploitation_detail is not None:
            rich.print(
                panel.Panel(
                    markdown.Markdown(vulnerability.exploitation_detail),
                    title="Exploitation details",
                )
            )
        if vulnerability.post_exploitation_detail is not None:
            rich.print(
                panel.Panel(
                    markdown.Markdown(vulnerability.post_exploitation_detail),
                    title="Post Exploitation details",
                )
            )

    def describe_vuln(self, scan_id: int, vuln_id: int) -> None:
        try:
            with models.Database() as session:
                vulnerabilities = []
                if vuln_id is not None:
                    vulnerability = typing.cast(
                        "orm.Query[models.Vulnerability]",
                        session.query(models.Vulnerability),
                    ).get(vuln_id)
                    vulnerabilities.append(vulnerability)
                elif scan_id is not None:
                    vulnerabilities = (
                        typing.cast(
                            "orm.Query[models.Vulnerability]",
                            session.query(models.Vulnerability),
                        )
                        .filter_by(scan_id=scan_id)
                        .order_by(models.Vulnerability.title)
                        .all()
                    )
                for v in vulnerabilities:
                    self._print_vulnerability(v)
                console.success("Vulnerabilities listed successfully.")
        except sqlalchemy.exc.OperationalError:
            console.error("Vulnerability / scan not Found.")

    def dump_vulnz(self, scan_id: int, dumper: dumpers.VulnzDumper) -> None:
        """Dump found vulnerabilities of a scan in a specific format."""
        vulnerabilities = []
        with models.Database() as session:
            severity_sort_logic: sqlalchemy.sql.elements.Label[sqlalchemy.Integer] = (
                case(
                    value=models.Vulnerability.risk_rating,
                    whens=risk_rating.RATINGS_ORDER,
                ).label("severity")
            )
            vulnerabilities = (
                typing.cast(
                    "orm.Query[models.Vulnerability]",
                    session.query(models.Vulnerability),
                )
                .filter_by(scan_id=scan_id)
                .order_by(severity_sort_logic)
                .all()
            )
        vulnz_list = []
        for vulnerability in vulnerabilities:
            vuln = {
                "id": vulnerability.id,
                "risk_rating": typing.cast(
                    risk_rating.RiskRating, vulnerability.risk_rating
                ).value,
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

    def link_agent_group_scan(
        self,
        scan: models.Scan,
        agent_group_definition: definitions.AgentGroupDefinition,
    ) -> None:
        """Link the agent group to the scan in the database.

        Args:
            scan: The scan object.
            agent_group_definition: The agent group definition.
        """
        with models.Database() as session:
            agent_group_db = models.AgentGroup.create_from_agent_group_definition(
                agent_group_definition
            )
            scan.agent_group_id = agent_group_db.id
            session.add(scan)
            session.commit()

    def link_assets_scan(
        self,
        scan_id: int,
        assets: typing.Optional[builtins.list[base_asset.Asset]] = None,
    ) -> None:
        """Link the assets to the scan in the database.

        Args:
            scan_id: The scan id.
            assets: The list of assets.
        """
        if assets is not None:
            models.Asset.create_from_assets_definition(scan_id=scan_id, assets=assets)
