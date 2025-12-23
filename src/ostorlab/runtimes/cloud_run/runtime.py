"""Cloud Run runtime runs agents on Google Cloud Run.

The Cloud Run runtime deploys agents as Cloud Run services, using external RabbitMQ and Redis services
that are accessible over the internet. This allows for scalable agent execution without requiring
Docker Swarm or local container orchestration.
"""

import logging
import re
import time
from typing import Dict, List, Optional
from concurrent import futures

import click
import sqlalchemy
import tenacity
from google.cloud import run_v2
from google.api import launch_stage_pb2

from ostorlab import exceptions
from ostorlab.assets import asset as base_asset
from ostorlab.cli import console as cli_console
from ostorlab.cli import install_agent
from ostorlab.runtimes import definitions
from ostorlab.runtimes import runtime
from ostorlab.runtimes.cloud_run import agent_runtime
from ostorlab.runtimes.local.models.models import Database
from ostorlab.runtimes.local.models import models
from ostorlab.runtimes.cloud_run.services import mq
from ostorlab.utils import risk_rating
from ostorlab.utils import styles

NETWORK_PREFIX = "ostorlab_cloud_run_network"

logger = logging.getLogger(__name__)
console = cli_console.Console()

ASSET_INJECTION_AGENT_DEFAULT = "agent/ostorlab/inject_asset"
TRACKER_AGENT_DEFAULT = "agent/ostorlab/tracker"
CLOUD_PERSIST_VULNZ_AGENT_DEFAULT = "agent/ostorlab/cloud_persist_vulnz"

DEFAULT_AGENTS = [
    ASSET_INJECTION_AGENT_DEFAULT,
    TRACKER_AGENT_DEFAULT,
    CLOUD_PERSIST_VULNZ_AGENT_DEFAULT,
]


class CloudRunError(exceptions.OstorlabError):
    """Cloud Run specific error."""


class MissingGCPConfiguration(CloudRunError):
    """Missing GCP configuration."""


class MissingAgentImage(CloudRunError):
    """Agent missing container image."""


class CloudRunRuntime(runtime.Runtime):
    """Cloud Run runtime deploys agents to Google Cloud Run.

    This runtime uses external MQ and Redis services that are accessible over the internet.
    Agents are deployed as Cloud Run services with proper environment configuration.
    """

    def __init__(
        self,
        *args,  # pylint: disable=W0613
        scan_id: str,
        bus_url: str,
        bus_vhost: str,
        bus_management_url: str,
        bus_exchange_topic: str,
        redis_url: str,
        gcp_project_id: str,
        gcp_region: str,
        gcp_service_account: Optional[str] = None,
        tracing_collector_url: Optional[str] = None,
        **kwargs,  # pylint: disable=W0613
    ) -> None:
        """Initialize Cloud Run runtime.

        Args:
            scan_id: Unique scan identifier.
            bus_url: RabbitMQ URL accessible over the internet.
            bus_vhost: RabbitMQ virtual host.
            bus_management_url: RabbitMQ management URL.
            bus_exchange_topic: RabbitMQ exchange topic.
            redis_url: Redis URL accessible over the internet.
            gcp_project_id: Google Cloud project ID.
            gcp_region: Google Cloud region for deployment.
            gcp_service_account: Service account for Cloud Run services.
            tracing_collector_url: Optional tracing collector URL.
        """
        super().__init__()
        self._scan_id = scan_id
        self._bus_url = bus_url
        self._bus_vhost = bus_vhost
        self._bus_management_url = bus_management_url
        self._bus_exchange_topic = bus_exchange_topic
        self._redis_url = redis_url
        self._tracing_collector_url = tracing_collector_url
        self._gcp_project_id = gcp_project_id
        self._gcp_region = gcp_region
        self._gcp_service_account = gcp_service_account

        # Initialize Cloud Run client
        self._client = run_v2.ServicesClient()

        # Track deployed services
        self._deployed_services: List[str] = []

    @property
    def name(self) -> str:
        """Runtime name."""
        return "cloud_run"

    @property
    def network(self) -> str:
        """Local runtime network name.

        Returns:
            Local runtime network name.
        """
        return f"{NETWORK_PREFIX}_{self.name}"

    def can_run(self, agent_group_definition: definitions.AgentGroupDefinition) -> bool:
        """Checks if the runtime can run the provided agent group definition.

        For Cloud Run, we need to verify:
        - All required GCP configurations are provided
        - Agents have valid container images

        Args:
            agent_group_definition: The agent group definition.

        Returns:
            True if can run, false otherwise.
        """
        # Check GCP configuration
        if not self._gcp_project_id or not self._gcp_region:
            console.error(
                "GCP project ID and region are required for Cloud Run runtime"
            )
            return False

        # Check external services configuration
        if not self._bus_url or not self._redis_url:
            console.error(
                "External MQ and Redis URLs are required for Cloud Run runtime"
            )
            return False

        # Check agents have container images
        for agent in agent_group_definition.agents:
            if not agent.container_image:
                console.error(f"Agent {agent.key} does not have a container image")
                return False

        return True

    def scan(
        self,
        title: str,
        agent_group_definition: definitions.AgentGroupDefinition,
        assets: Optional[List[base_asset.Asset]],
    ) -> Optional[models.Scan]:
        """Triggers a scan using the provided agent group definition and asset target.

        Args:
            title: Scan title
            agent_group_definition: The agent group to run.
            assets: The scan target assets.

        Returns:
            Scan object if created successfully, None otherwise.
        """
        with models.Database() as session:
            try:
                # Create scan in database
                scan = models.Scan.create(
                    title=title,
                    asset=assets[0].__class__.__name__ if assets else "unknown",
                )
                console.info(f"Created scan with ID: {scan.id}")

                # Start agent deployment
                self._start_agents(agent_group_definition, scan.id)

                # Inject assets if provided
                if assets:
                    self._inject_assets(assets, scan.id)

                return scan

            except sqlalchemy.exc.IntegrityError as e:
                console.error(f"Failed to create scan: {e}")
                return None

    def _start_mq_service(self):
        """Start a local rabbitmq service."""
        self._mq_service = mq.CloudRunRabbitMQ(name=self.name, network=self.network)
        self._mq_service.start()
        if "mq" in self.follow:
            self._log_streamer.stream(self._mq_service.service)

    def _start_agents(
        self, agent_group_definition: definitions.AgentGroupDefinition, scan_id: int
    ) -> None:
        """Deploy agents to Cloud Run.

        Args:
            agent_group_definition: Agent group to deploy.
            scan_id: Scan ID for labeling resources.
        """
        console.info("Deploying agents to Cloud Run...")

        with futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_agent = {}

            for agent in agent_group_definition.agents:
                # Skip if no container image
                if not agent.container_image:
                    console.warning(f"Skipping agent {agent.key} - no container image")
                    continue

                # Create agent runtime and deploy
                agent_runtime_instance = agent_runtime.CloudRunAgentRuntime(
                    agent_settings=agent,
                    runtime_name=self.name,
                    scan_id=scan_id,
                    bus_url=self._bus_url,
                    bus_vhost=self._bus_vhost,
                    bus_exchange_topic=self._bus_exchange_topic,
                    redis_url=self._redis_url,
                    gcp_project_id=self._gcp_project_id,
                    gcp_region=self._gcp_region,
                    gcp_service_account=self._gcp_service_account,
                    tracing_collector_url=self._tracing_collector_url,
                )

                # Submit deployment task
                future = executor.submit(
                    agent_runtime_instance.deploy_service, scan_id=scan_id
                )
                future_to_agent[future] = agent

            # Wait for all deployments
            for future in futures.as_completed(future_to_agent):
                agent = future_to_agent[future]
                try:
                    service_name = future.result()
                    console.info(f"Successfully deployed {agent.key} as {service_name}")
                    self._deployed_services.append(service_name)
                except Exception as e:
                    console.error(f"Failed to deploy {agent.key}: {e}")

    def _inject_assets(self, assets: List[base_asset.Asset], scan_id: int) -> None:
        """Inject assets by calling the asset injection agent.

        Args:
            assets: List of assets to inject.
            scan_id: Scan ID for correlation.
        """
        console.info("Injecting assets...")

        # For Cloud Run, we'll need to implement a way to trigger the injection
        # This could be done via a Cloud Function or by deploying a temporary service
        # For now, we'll log that this needs to be implemented
        console.info("Asset injection for Cloud Run runtime needs to be implemented")

    def stop(self, scan_id: str) -> None:
        """Stops a scan by deleting all deployed Cloud Run services.

        Args:
            scan_id: The scan ID.
        """
        console.info(f"Stopping scan {scan_id} and cleaning up Cloud Run services...")

        with futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_service = {}

            # Delete all deployed services for this scan
            for service_name in self._deployed_services:
                if str(scan_id) in service_name:
                    future = executor.submit(self._delete_service, service_name)
                    future_to_service[future] = service_name

            # Wait for deletions
            for future in futures.as_completed(future_to_service):
                service_name = future_to_service[future]
                try:
                    future.result()
                    console.info(f"Deleted service {service_name}")
                except Exception as e:
                    console.error(f"Failed to delete {service_name}: {e}")

    def _delete_service(self, service_name: str) -> None:
        """Delete a Cloud Run service.

        Args:
            service_name: Name of the service to delete.
        """
        service_path = f"projects/{self._gcp_project_id}/locations/{self._gcp_region}/services/{service_name}"

        try:
            self._client.delete_service(name=service_path)
        except Exception as e:
            logger.error(f"Error deleting service {service_name}: {e}")
            raise

    def list(self, page: int = 1, number_elements: int = 10) -> List[runtime.Scan]:
        """Lists scans managed by this runtime.

        Args:
            page: Page number for pagination.
            number_elements: Number of elements per page.

        Returns:
            List of scan objects.
        """
        with models.Database() as session:
            # Query scans created by this runtime
            # For now, return all scans - could be filtered by runtime type in future
            scans = (
                session.query(models.Scan)
                .order_by(models.Scan.created_time.desc())
                .limit(number_elements)
                .offset((page - 1) * number_elements)
                .all()
            )

            return [
                runtime.Scan(
                    id=str(scan.id),
                    created_time=scan.created_time.isoformat(),
                    progress=scan.progress.value if scan.progress else None,
                    asset=scan.asset,
                    risk_rating=scan.risk_rating.value if scan.risk_rating else None,
                )
                for scan in scans
            ]

    def install(self) -> None:
        """Install necessary components for Cloud Run runtime."""
        console.info("Cloud Run runtime does not require local installation.")
        console.info("Ensure you have:")
        console.info("  - Google Cloud SDK installed and configured")
        console.info("  - Proper GCP permissions for Cloud Run")
        console.info("  - External RabbitMQ and Redis services accessible")

    def dump_vulnz(self, scan_id: int, dumper: runtime.dumpers.VulnzDumper):
        """Dump vulnerabilities for a scan.

        Args:
            scan_id: The scan ID.
            dumper: Vulnerability dumper instance.
        """
        with models.Database() as session:
            vulnerabilities = (
                session.query(models.Vulnerability).filter_by(scan_id=scan_id).all()
            )

            for vulnerability in vulnerabilities:
                dumper.dump_vulnerability(
                    entry=vulnerability,
                    risk_rating=vulnerability.risk_rating,
                    cvss_v3_vector=vulnerability.cvss_v3_vector,
                    dna=vulnerability.dna,
                    location=vulnerability.location,
                )

    def link_agent_group_scan(
        self,
        scan,
        agent_group_definition: definitions.AgentGroupDefinition,
    ) -> None:
        """Link agent group to scan in database.

        Args:
            scan: The scan object.
            agent_group_definition: The agent group definition.
        """
        with models.Database() as session:
            models.AgentGroup.create(
                scan_id=scan.id,
                definition=agent_group_definition,
            )
            session.commit()

    def link_assets_scan(self, scan_id: int, assets: List[base_asset.Asset]) -> None:
        """Link assets to scan in database.

        Args:
            scan_id: The scan ID.
            assets: List of assets to link.
        """
        with models.Database() as session:
            for asset in assets:
                models.Asset.create(scan_id, asset)
            session.commit()
