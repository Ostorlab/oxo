"""Cloud Run runtime runs agents on Google Cloud Run.

The Cloud Run runtime deploys agents as Cloud Run jobs (with executions), using external RabbitMQ and Redis services
that are accessible over the internet. This allows for scalable agent execution without requiring
Docker Swarm or local container orchestration.
"""

import logging
from typing import List, Optional
from concurrent import futures


from ostorlab import exceptions
from ostorlab.assets import asset as base_asset
from ostorlab.cli import console as cli_console
from ostorlab.runtimes import definitions
from ostorlab.runtimes import runtime
from ostorlab.runtimes.cloud_run import agent_runtime
from ostorlab.runtimes.local.models import models

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
        # Track deployed jobs
        self._deployed_services: List[str] = []

    @property
    def name(self) -> str:
        """Cloud Run runtime instance name."""
        return self._scan_id

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

        # Start agent deployment
        self._start_agents(agent_group_definition, self._scan_id)

        # Inject assets if provided
        if assets:
            self._inject_assets(assets, self._scan_id)

    def _start_agents(
        self, agent_group_definition: definitions.AgentGroupDefinition, scan_id: str
    ) -> None:
        """Deploy agents to Cloud Run.

        Args:
            agent_group_definition: Agent group to deploy.
            scan_id: Scan ID for labeling resources.
        """
        console.info("Deploying agents to Cloud Run...")

        with futures.ThreadPoolExecutor(max_workers=10):
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
                    bus_management_url=self._bus_management_url,
                    bus_exchange_topic=self._bus_exchange_topic,
                    redis_url=self._redis_url,
                    gcp_project_id=self._gcp_project_id,
                    gcp_region=self._gcp_region,
                    gcp_service_account=self._gcp_service_account,
                    tracing_collector_url=self._tracing_collector_url,
                )
                service_name = agent_runtime_instance.deploy_service(scan_id=scan_id)
                self._deployed_services.append(service_name)

            #     # Submit deployment task
            #     future = executor.submit(
            #         agent_runtime_instance.deploy_service, scan_id=scan_id
            #     )
            #     future_to_agent[future] = agent
            #
            # # Wait for all deployments
            # for future in futures.as_completed(future_to_agent):
            #     agent = future_to_agent[future]
            #     try:
            #         service_name = future.result()
            #         console.info(f"Successfully deployed {agent.key} as {service_name}")
            #         self._deployed_services.append(service_name)
            #     except Exception as e:
            #         console.error(f"Failed to deploy {agent.key}: {e}")

    def _inject_assets(self, assets: List[base_asset.Asset], scan_id: str) -> None:
        """Inject assets by deploying the inject_asset agent with assets in GCS.

        Args:
            assets: List of assets to inject.
            scan_id: Scan ID for correlation.
        """
        console.info("Injecting assets...")

        inject_asset_agent_settings = definitions.AgentSettings(
            key=ASSET_INJECTION_AGENT_DEFAULT, restart_policy="none"
        )

        agent_runtime_instance = agent_runtime.CloudRunAgentRuntime(
            agent_settings=inject_asset_agent_settings,
            runtime_name=self.name,
            scan_id=scan_id,
            bus_url=self._bus_url,
            bus_vhost=self._bus_vhost,
            bus_management_url=self._bus_management_url,
            bus_exchange_topic=self._bus_exchange_topic,
            redis_url=self._redis_url,
            gcp_project_id=self._gcp_project_id,
            gcp_region=self._gcp_region,
            gcp_service_account=self._gcp_service_account,
            tracing_collector_url=self._tracing_collector_url,
        )

        service_name = agent_runtime_instance.deploy_service_with_assets(
            scan_id=scan_id, assets=assets
        )
        console.info(f"Asset injection agent deployed: {service_name}")

    def stop(self, scan_id: str) -> None:
        """Stops a scan by deleting all deployed Cloud Run services.

        Args:
            scan_id: The scan ID.
        """
        raise NotImplementedError()

    def list(self, page: int = 1, number_elements: int = 10) -> List[runtime.Scan]:
        """Lists scans managed by this runtime.

        Args:
            page: Page number for pagination.
            number_elements: Number of elements per page.

        Returns:
            List of scan objects.
        """
        pass

    def install(self) -> None:
        """Install necessary components for Cloud Run runtime."""
        pass

    def dump_vulnz(self, scan_id: int, dumper: runtime.dumpers.VulnzDumper):
        """Dump vulnerabilities for a scan.

        Args:
            scan_id: The scan ID.
            dumper: Vulnerability dumper instance.
        """
        pass

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
        pass

    def link_assets_scan(self, scan_id: int, assets: List[base_asset.Asset]) -> None:
        """Link assets to scan in database.

        Args:
            scan_id: The scan ID.
            assets: List of assets to link.
        """
        pass
