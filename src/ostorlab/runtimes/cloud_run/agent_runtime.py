"""Cloud Run agent runtime implementation.

Adapts lite_local AgentRuntime behavior to Google Cloud Run Jobs. It stores agent
settings, definition, and mounts in a per-job GCS bucket and restores them in the
job container before starting the agent.
"""

import io
import logging
import random
import uuid
from resource import RLIMIT_CPU
from typing import List, Optional, Tuple

import docker
from google.cloud import run_v2
from google.cloud import storage
from google.cloud.storage import Bucket

from ostorlab import configuration_manager
from ostorlab import exceptions
from ostorlab.agent import definitions as agent_definitions
from ostorlab.runtimes import definitions
from ostorlab.assets import asset as base_asset

logger = logging.getLogger(__name__)

MOUNT_VARIABLES = {"$CONFIG_HOME": str(configuration_manager.OSTORLAB_PRIVATE_DIR)}

HEALTHCHECK_HOST = "0.0.0.0"
HEALTHCHECK_PORT = 5000
MAX_SERVICE_NAME_LEN = 63
MAX_RANDOM_NAME_LEN = 5


class Error(exceptions.OstorlabError):
    """Base Error."""


class MissingAgentDefinitionLabel(Error):
    """Agent definition label is missing from the agent image."""


class ServiceNameTooLong(Error):
    """Raised when the agent definition service_name exceeds the maximum allowed length."""


class CloudRunAgentRuntime:
    """Cloud Run Agent Runtime that deploys agents as Cloud Run Jobs."""

    def __init__(
        self,
        agent_settings: definitions.AgentSettings,
        runtime_name: str,
        scan_id: str,
        bus_url: str,
        bus_vhost: str,
        bus_exchange_topic: str,
        bus_management_url: str,
        redis_url: str,
        gcp_project_id: str,
        gcp_region: str,
        gcp_service_account: Optional[str] = None,
        tracing_collector_url: Optional[str] = None,
        gcp_logging_credential: Optional[str] = None,
    ) -> None:
        self.agent = agent_settings
        self.runtime_name = runtime_name
        self.scan_id = scan_id
        self.bus_url = bus_url
        self.bus_vhost = bus_vhost
        self.bus_exchange_topic = bus_exchange_topic
        self.bus_management_url = bus_management_url
        self.redis_url = redis_url
        self._gcp_project_id = gcp_project_id
        self._gcp_region = gcp_region
        self._gcp_service_account = gcp_service_account
        self._tracing_collector_url = tracing_collector_url
        self._gcp_logging_credential = gcp_logging_credential
        self._jobs_client = run_v2.JobsClient.from_service_account_file(
            self._gcp_service_account
        )
        self.update_agent_settings_for_cloud()

    def update_agent_settings_for_cloud(self) -> None:
        """Update agent settings with Cloud Run runtime values."""
        self.agent.bus_url = self.bus_url
        self.agent.bus_exchange_topic = self.bus_exchange_topic
        self.agent.bus_management_url = self.bus_management_url
        self.agent.bus_vhost = self.bus_vhost
        self.agent.healthcheck_host = HEALTHCHECK_HOST
        self.agent.healthcheck_port = HEALTHCHECK_PORT
        self.agent.redis_url = self.redis_url
        self.agent.tracing_collector_url = self._tracing_collector_url

    def _load_agent_definition_and_label(
        self,
    ) -> Tuple[agent_definitions.AgentDefinition, str]:
        """Load agent definition and raw YAML string from image label."""
        docker_client = docker.from_env()
        docker_image = docker_client.images.get(self.agent.container_image)
        yaml_definition_string = docker_image.labels.get("agent_definition")
        if yaml_definition_string is None:
            raise MissingAgentDefinitionLabel(
                f"agent definition label is missing from image {docker_image.tags[0]}"
            )
        with io.StringIO(yaml_definition_string) as file:
            agent_definition = agent_definitions.AgentDefinition.from_yaml(file)
        return agent_definition, yaml_definition_string

    def _build_service_name(
        self, agent_definition: agent_definitions.AgentDefinition
    ) -> str:
        if agent_definition.service_name is not None:
            if len(agent_definition.service_name) > MAX_SERVICE_NAME_LEN:
                raise ServiceNameTooLong(
                    f'service name "{agent_definition.service_name}" exceeds max length of {MAX_SERVICE_NAME_LEN}'
                )
            return agent_definition.service_name

        service_name = (
            self.agent.container_image.split(":")[0].replace(".", "")
            + "_"
            + self.runtime_name
        )
        if len(service_name) + MAX_RANDOM_NAME_LEN < MAX_SERVICE_NAME_LEN:
            service_name = service_name + "_" + str(random.randrange(0, 9999))

        service_name = service_name.replace("_", "-")
        return service_name

    def _serialize_settings_bytes(self) -> bytes:
        return self.agent.to_raw_proto()

    def _serialize_definition_bytes(self, yaml_definition: str) -> bytes:
        return yaml_definition.encode()

    def _storage_client(self) -> storage.Client:
        return storage.Client.from_service_account_json(self._gcp_service_account)

    def _create_bucket(self, client: storage.Client, bucket_prefix: str) -> Bucket:
        # Bucket names must be globally unique, 3-63 chars, lowercase, start with letter/number.
        base = bucket_prefix.lower()
        candidate = f"{base}-{uuid.uuid4().hex[:8]}"
        bucket = client.create_bucket(candidate, location=self._gcp_region)
        return bucket

    def _upload_blob(self, bucket: Bucket, blob_name: str, data: bytes) -> None:
        blob = bucket.blob(blob_name)
        blob.upload_from_string(data)

    def _prepare_artifacts(
        self,
        settings_bytes: bytes | None = None,
        definition_bytes: bytes | None = None,
        asset_files: Optional[dict[str, bytes]] = None,
    ) -> str:
        """Prepare artifacts by uploading to GCS bucket.

        Args:
            settings_bytes: Serialized agent settings (can be empty if in asset_files).
            definition_bytes: Serialized agent definition (can be empty if in asset_files).
            asset_files: Optional dict of asset filenames to their binary content.

        Returns:
            Bucket name containing the artifacts.
        """
        client = self._storage_client()
        bucket_prefix = f"ostorlab-{self._gcp_project_id}-{self.runtime_name}-{random.randrange(0, 9999)}"[
            :50
        ]
        bucket = self._create_bucket(client, bucket_prefix)

        if settings_bytes is not None and definition_bytes is not None:
            settings_blob_name = "settings.binproto"
            definition_blob_name = "ostorlab.yaml"

            self._upload_blob(bucket, settings_blob_name, settings_bytes)
            self._upload_blob(bucket, definition_blob_name, definition_bytes)

        if asset_files:
            for filename, content in asset_files.items():
                self._upload_blob(bucket, filename, content)

        return bucket.name

    def _build_gcs_bucket_volume(
        self, bucket_name: str, mount_path: str = "/tmp"
    ) -> tuple[List[run_v2.Volume], List[run_v2.VolumeMount]]:
        """Build GCS bucket volume and mount.

        Args:
            bucket_name: Name of the GCS bucket.
            mount_path: Path where to mount the bucket in the container.
                       Default is "/tmp" where agents expect config files.

        Returns:
            Tuple of volumes and volume mounts.
        """
        name = f"gcs-bucket-{random.randrange(0, 9999)}"
        volume = run_v2.Volume(
            name=name,
            gcs=run_v2.GCSVolumeSource(bucket=bucket_name),
        )
        volume_mount = run_v2.VolumeMount(name=name, mount_path=mount_path)
        return [volume], [volume_mount]

    def _build_mount_envs(self, mounts: List[str]) -> List[tuple[str, str]]:
        mount_envs = []
        for idx, mount in enumerate(mounts):
            _, target, _ = self._parse_mount(mount)
            mount_envs.append((f"OSTORLAB_MOUNT_{idx}_DST", target))
        return mount_envs

    def _build_env(self, extra_envs: List[tuple[str, str]]) -> List[run_v2.EnvVar]:
        envs = [
            ("UNIVERSE", self.runtime_name),
        ]
        envs.extend(extra_envs)
        return [run_v2.EnvVar(name=name, value=value) for name, value in envs]

    def deploy_service(self, scan_id: str) -> str:
        """Create and run a Cloud Run Job for the agent.

        Args:
            scan_id: Scan identifier, used for labeling.

        Returns:
            The Cloud Run Job name.
        """
        agent_definition, yaml_definition_string = (
            self._load_agent_definition_and_label()
        )

        # Apply defaults from definition.
        self.agent.open_ports = self.agent.open_ports or agent_definition.open_ports
        self.agent.mounts = self.agent.mounts or agent_definition.mounts
        self.agent.constraints = self.agent.constraints or agent_definition.constraints
        self.agent.mem_limit = self.agent.mem_limit or agent_definition.mem_limit
        self.agent.restart_policy = (
            self.agent.restart_policy or agent_definition.restart_policy or "any"
        )
        self.agent.caps = self.agent.caps or agent_definition.caps

        if self.agent.open_ports:
            logger.warning(
                "Cloud Run Jobs do not expose open_ports; ignoring declared ports."
            )

        settings_bytes = self._serialize_settings_bytes()
        definition_bytes = self._serialize_definition_bytes(yaml_definition_string)

        bucket_name = self._prepare_artifacts(settings_bytes, definition_bytes)

        volumes, volume_mounts = self._build_gcs_bucket_volume(bucket_name)

        env_pairs = []
        env_vars = self._build_env(env_pairs)

        container = run_v2.Container()
        # TODO: Hack to make images work. Should be fixed.
        container.image = (
            f"ostorlab/{self.agent.container_image.replace('ostorlab', '5448')}"
        )
        container.env = env_vars
        container.volume_mounts = volume_mounts
        task_template = run_v2.TaskTemplate()
        task_template.containers = [container]
        task_template.volumes = volumes
        task_template.max_retries = 0

        execution_template = run_v2.ExecutionTemplate()
        execution_template.template = task_template
        execution_template.task_count = 1
        execution_template.parallelism = 1
        execution_template.resources = run_v2.ResourceRequirements(
            limits={
                "cpu": "8",
                "memory": "8Gi",
            }
        )


        job = run_v2.Job()
        job.template = execution_template
        # TODO: labels not working.
        # job.labels = {
        #     "ostorlab.universe": self.runtime_name,
        #     "scan_id": scan_id,
        #     "agent": self.agent.key,
        # }

        job_id = self._build_service_name(agent_definition)
        parent = f"projects/{self._gcp_project_id}/locations/{self._gcp_region}"
        job_name = f"{parent}/jobs/{job_id}"

        self._jobs_client.create_job(
            parent=parent,
            job=job,
            job_id=job_id,
        )
        logger.info("Created Cloud Run Job %s", job_name)
        self._jobs_client.run_job(name=job_name)
        return job_name

    def deploy_service_with_assets(
        self, scan_id: str, assets: List["base_asset.Asset"]
    ) -> str:
        """Deploy inject_asset agent with assets uploaded to GCS.

        Args:
            scan_id: Scan identifier.
            assets: List of assets to inject.

        Returns:
            The Cloud Run Job name.
        """
        agent_definition, yaml_definition_string = (
            self._load_agent_definition_and_label()
        )

        self.agent.open_ports = self.agent.open_ports or agent_definition.open_ports
        self.agent.mounts = self.agent.mounts or agent_definition.mounts
        self.agent.constraints = self.agent.constraints or agent_definition.constraints
        self.agent.mem_limit = self.agent.mem_limit or agent_definition.mem_limit
        self.agent.restart_policy = (
            self.agent.restart_policy or agent_definition.restart_policy or "none"
        )
        self.agent.caps = self.agent.caps or agent_definition.caps

        settings_bytes = self._serialize_settings_bytes()
        definition_bytes = self._serialize_definition_bytes(yaml_definition_string)

        asset_files = {}
        asset_files["settings.binproto"] = settings_bytes
        asset_files["ostorlab.yaml"] = definition_bytes
        bucket_name = self._prepare_artifacts(asset_files=asset_files)

        volumes = []
        volume_mounts = []

        volumes_tmp, volume_mounts_tmp = self._build_gcs_bucket_volume(
            bucket_name, mount_path="/tmp"
        )
        volumes.extend(volumes_tmp)
        volume_mounts.extend(volume_mounts_tmp)

        asset_files = {}
        for i, asset in enumerate(assets):
            asset_files[f"asset.binproto_{i}"] = asset.to_proto()
            asset_files[f"selector.txt_{i}"] = asset.selector.encode()

        bucket_name = self._prepare_artifacts(asset_files=asset_files)
        volumes_asset, volume_mounts_asset = self._build_gcs_bucket_volume(
            bucket_name, mount_path="/asset"
        )
        volumes.extend(volumes_asset)
        volume_mounts.extend(volume_mounts_asset)

        env_pairs = []
        env_vars = self._build_env(env_pairs)

        container = run_v2.Container()
        # TODO: Hack to make images work. Should be fixed.
        container.image = (
            f"ostorlab/{self.agent.container_image.replace('ostorlab', '5448')}"
        )
        container.env = env_vars
        container.volume_mounts = volume_mounts

        task_template = run_v2.TaskTemplate()
        task_template.containers = [container]
        task_template.volumes = volumes
        task_template.max_retries = 0

        execution_template = run_v2.ExecutionTemplate()
        execution_template.template = task_template
        execution_template.task_count = 1
        execution_template.parallelism = 1
        execution_template.resources = run_v2.ResourceRequirements(
            limits={
                "cpu": "8",
                "memory": "8Gi",
            }
        )


        job = run_v2.Job()
        job.template = execution_template

        job_id = self._build_service_name(agent_definition)
        parent = f"projects/{self._gcp_project_id}/locations/{self._gcp_region}"
        job_name = f"{parent}/jobs/{job_id}"

        self._jobs_client.create_job(
            parent=parent,
            job=job,
            job_id=job_id,
        )
        logger.info("Created inject_asset Cloud Run Job %s", job_name)
        self._jobs_client.run_job(name=job_name)
        return job_name
