"""Cloud Run agent runtime implementation.

Adapts lite_local AgentRuntime behavior to Google Cloud Run Jobs. It injects agent
settings and definition as in-memory volumes and copies host mounts into Cloud Run
empty_dir volumes before starting the agent.
"""

import base64
import io
import logging
import os
import random
import tarfile
import tempfile
from typing import List, Optional, Tuple

import docker
from docker import errors as docker_errors
from google.api_core import exceptions as gcp_exceptions
from google.cloud import run_v2

from ostorlab import configuration_manager
from ostorlab import exceptions
from ostorlab.agent import definitions as agent_definitions
from ostorlab.runtimes import definitions

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
        self._jobs_client = run_v2.JobsClient.from_service_account_file(self._gcp_service_account)
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

    def replace_variable_mounts(self, mounts: List[str]) -> List[str]:
        """Replace path variables for the container mounts."""
        replaced_mounts = []
        for mount in mounts:
            for mount_variable, mount_value in MOUNT_VARIABLES.items():
                mount = mount.replace(mount_variable, mount_value)
            replaced_mounts.append(mount)
        return replaced_mounts

    def _build_service_name(self, agent_definition: agent_definitions.AgentDefinition) -> str:
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

    def _serialize_settings(self) -> str:
        agent_instance_settings_proto = self.agent.to_raw_proto()
        return base64.b64encode(agent_instance_settings_proto).decode()

    def _serialize_definition(self, yaml_definition: str) -> str:
        return base64.b64encode(yaml_definition.encode()).decode()

    def _parse_mount(self, mount: str) -> tuple[str, str, Optional[str]]:
        parts = mount.split(":")
        if len(parts) < 2:
            raise docker_errors.InvalidArgument(f'invalid mount format "{mount}"')
        source = parts[0]
        target = parts[1]
        mode = parts[2] if len(parts) >= 3 else None
        return source, target, mode

    def _encode_mount_payload(self, source: str) -> tuple[str, bool]:
        if not os.path.exists(source):
            raise FileNotFoundError(f"mount source {source} does not exist")
        if os.path.isdir(source):
            with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=True) as tmp:
                with tarfile.open(tmp.name, "w:gz") as tar:
                    tar.add(source, arcname=".")
                tmp.seek(0)
                data = tmp.read()
            return base64.b64encode(data).decode(), True
        with open(source, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode(), False

    def _build_mounts(self, mounts: List[str]):
        volumes: List[run_v2.Volume] = []
        volume_mounts: List[run_v2.VolumeMount] = []
        mount_envs = []

        for idx, mount in enumerate(mounts):
            source, target, _ = self._parse_mount(mount)
            payload_b64, is_dir = self._encode_mount_payload(source)
            volume_name = f"mount-{idx}"
            volumes.append(
                run_v2.Volume(
                    name=volume_name,
                    empty_dir=run_v2.EmptyDirVolumeSource(
                        medium=run_v2.EmptyDirVolumeSource.Medium.MEMORY
                    ),
                )
            )
            mount_path = target if target.endswith("/") else os.path.dirname(target) or "/"
            volume_mounts.append(
                run_v2.VolumeMount(name=volume_name, mount_path=mount_path)
            )
            mount_envs.append((f"OSTORLAB_MOUNT_{idx}_DST", target))
            mount_envs.append((f"OSTORLAB_MOUNT_{idx}_CONTENT_B64", payload_b64))
            mount_envs.append((f"OSTORLAB_MOUNT_{idx}_IS_DIR", "1" if is_dir else "0"))
        return volumes, volume_mounts, mount_envs

    def _build_env(self, extra_envs: List[tuple[str, str]]) -> List[run_v2.EnvVar]:
        envs = [
            ("UNIVERSE", self.runtime_name),
        ]
        if self._gcp_logging_credential is not None:
            envs.append(
                (
                    "GCP_LOGGING_CREDENTIAL",
                    base64.b64encode(self._gcp_logging_credential.encode()).decode(),
                )
            )
        envs.extend(extra_envs)
        return [run_v2.EnvVar(name=name, value=value) for name, value in envs]

    def _build_startup_script(self) -> str:
        lines = [
            "set -e",
            "mkdir -p /tmp/ostorlab",
            "echo \"$AGENT_SETTINGS_B64\" | base64 -d > /tmp/ostorlab/settings.binproto",
            "echo \"$AGENT_DEFINITION_B64\" | base64 -d > /tmp/ostorlab/ostorlab.yaml",
            "i=0",
            "while true; do",
            '  dst_var=\\"OSTORLAB_MOUNT_${i}_DST\\"',
            '  content_var=\\"OSTORLAB_MOUNT_${i}_CONTENT_B64\\"',
            '  dir_var=\\"OSTORLAB_MOUNT_${i}_IS_DIR\\"',
            "  dst=${!dst_var}",
            "  [ -z \"$dst\" ] && break",
            "  payload=${!content_var}",
            "  is_dir=${!dir_var}",
            "  if [ -n \"$payload\" ]; then",
            "    if [ \"$is_dir\" = \"1\" ]; then",
            "      mkdir -p \"$dst\"",
            "      echo \"$payload\" | base64 -d | tar -xz -C \"$dst\"",
            "    else",
            "      mkdir -p \"$(dirname \"$dst\")\"",
            "      echo \"$payload\" | base64 -d > \"$dst\"",
            "    fi",
            "  fi",
            "  i=$((i+1))",
            "done",
            "exec ostorlab agent run",
        ]
        return "\n".join(lines)

    def deploy_service(self, scan_id: str) -> str:
        """Create and run a Cloud Run Job for the agent.

        Args:
            scan_id: Scan identifier, used for labeling.

        Returns:
            The Cloud Run Job name.
        """
        agent_definition, yaml_definition_string = self._load_agent_definition_and_label()

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
            logger.warning("Cloud Run Jobs do not expose open_ports; ignoring declared ports.")

        mounts = self.replace_variable_mounts(self.agent.mounts or [])
        volumes, volume_mounts, mount_envs = self._build_mounts(mounts)

        settings_b64 = self._serialize_settings()
        definition_b64 = self._serialize_definition(yaml_definition_string)

        volumes.append(
            run_v2.Volume(
                name="settings-volume",
                empty_dir=run_v2.EmptyDirVolumeSource(
                    medium=run_v2.EmptyDirVolumeSource.Medium.MEMORY
                ),
            )
        )
        volume_mounts.append(
            run_v2.VolumeMount(name="settings-volume", mount_path="/tmp/ostorlab")
        )

        env_pairs = [
            ("AGENT_SETTINGS_B64", settings_b64),
            ("AGENT_DEFINITION_B64", definition_b64),
        ]
        env_pairs.extend(mount_envs)

        env_vars = self._build_env(env_pairs)

        container = run_v2.Container()
        # TODO: Hack to make images work. Should be fixed.
        container.image = f"ostorlab/{self.agent.container_image.replace('ostorlab', '5448')}"
        container.command = ["/bin/sh"]
        container.args = ["-c", self._build_startup_script()]
        container.env = env_vars
        container.volume_mounts = volume_mounts
        if self.agent.mem_limit is not None:
            container.resources = run_v2.ResourceRequirements(
                limits={"memory": str(self.agent.mem_limit)}
            )

        task_template = run_v2.TaskTemplate()
        task_template.containers = [container]
        task_template.volumes = volumes
        # task_template.service_account = self._gcp_service_account
        task_template.max_retries = 0

        execution_template = run_v2.ExecutionTemplate()
        execution_template.template = task_template
        execution_template.task_count = 1
        execution_template.parallelism = 1

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

        try:
            self._jobs_client.get_job(name=job_name)
            logger.info("Job %s already exists; reusing.", job_name)
        except gcp_exceptions.NotFound:
            try:
                self._jobs_client.create_job(
                    parent=parent,
                    job=job,
                    job_id=job_id,
                )
                logger.info("Created Cloud Run Job %s", job_name)
            except gcp_exceptions.AlreadyExists:
                job_id = job_id + "-" + str(random.randrange(0, 9999))
                job_name = f"{parent}/jobs/{job_id}"
                self._jobs_client.create_job(
                    parent=parent,
                    job=job,
                    job_id=job_id,
                )
                logger.info("Created Cloud Run Job with suffix %s", job_name)

        self._jobs_client.run_job(name=job_name)
        return job_name
