"""Cloud Run agent runtime for deploying agents to Google Cloud Run.

This module handles creating and managing Cloud Run jobs for Ostorlab agents.
"""

import logging
import re
import uuid
from typing import Dict, Optional, Any

from google.cloud import run_v2
from google.api import launch_stage_pb2

from ostorlab.runtimes import definitions

logger = logging.getLogger(__name__)

MAX_SERVICE_NAME_LEN = 63
MAX_RANDOM_NAME_LEN = 5


class Error(Exception):
    """Custom error for Cloud Run agent runtime."""


class CloudRunError(Error):
    """Custom error for Cloud Run agent runtime."""


class CloudRunAgentRuntime:
    """Responsible for creating and managing Cloud Run services for agents."""

    def __init__(
        self,
        agent_settings: definitions.AgentSettings,
        runtime_name: str,
        scan_id: int,
        bus_url: str,
        bus_vhost: str,
        bus_exchange_topic: str,
        redis_url: str,
        gcp_project_id: str,
        gcp_region: str,
        gcp_service_account: Optional[str] = None,
        tracing_collector_url: Optional[str] = None,
    ) -> None:
        """Initialize Cloud Run agent runtime.

        Args:
            agent_settings: Agent settings and configuration.
            runtime_name: Name of the runtime (cloud_run).
            scan_id: Scan ID for resource naming.
            bus_url: RabbitMQ URL.
            bus_vhost: RabbitMQ virtual host.
            bus_exchange_topic: RabbitMQ exchange topic.
            redis_url: Redis URL.
            gcp_project_id: GCP project ID.
            gcp_region: GCP region for deployment.
            gcp_service_account: Service account for Cloud Run.
            tracing_collector_url: Optional tracing collector URL.
            bus_ip: RabbitMQ IP address for external access.
            redis_ip: Redis IP address for external access.
        """
        self._agent_settings = agent_settings
        self._runtime_name = runtime_name
        self._scan_id = scan_id
        self._bus_url = bus_url
        self._bus_vhost = bus_vhost
        self._bus_exchange_topic = bus_exchange_topic
        self._redis_url = redis_url
        self._gcp_project_id = gcp_project_id
        self._gcp_region = gcp_region
        self._gcp_service_account = gcp_service_account
        self._tracing_collector_url = tracing_collector_url

        # Initialize Cloud Run Jobs clients
        self._client = run_v2.JobsClient()
        self._executions_client = run_v2.ExecutionsClient()

        # Generate job name
        self._service_name = self._generate_service_name()

    @property
    def service_name(self) -> str:
        """Get the generated service name."""
        return self._service_name

    def _generate_service_name(self) -> str:
        """Generate a valid Cloud Run service name.

        Cloud Run service names must:
        - Be 1-63 characters long
        - Match regex [a-z]([-a-z0-9]*[a-z0-9])?
        - Contain only lowercase letters, numbers, and hyphens

        Returns:
            Valid service name.
        """
        # Clean agent key to be DNS compliant
        agent_key_clean = re.sub(r"[^a-z0-9-]", "-", self._agent_settings.key.lower())

        # Create base name
        base_name = f"ostorlab-{self._scan_id}-{agent_key_clean}"

        # Ensure it starts with a letter
        if not base_name[0].isalpha():
            base_name = f"a-{base_name}"

        # Truncate if too long, preserving scan_id
        if len(base_name) > MAX_SERVICE_NAME_LEN:
            # Keep scan_id and add hash of agent key
            prefix = f"ostorlab-{self._scan_id}"
            remaining_length = MAX_SERVICE_NAME_LEN - len(prefix) - 1
            if remaining_length > 0:
                agent_hash = str(uuid.uuid5(uuid.NAMESPACE_DNS, agent_key_clean))[
                    :remaining_length
                ]
                base_name = f"{prefix}-{agent_hash}"
            else:
                # Fallback if scan_id is too long
                base_name = f"ostorlab-scan-{self._scan_id}"[:MAX_SERVICE_NAME_LEN]

        # Ensure it ends with alphanumeric
        if not base_name[-1].isalnum():
            base_name = base_name.rstrip("-") + "0"
            base_name = base_name[:MAX_SERVICE_NAME_LEN]

        return base_name

    def _prepare_environment_variables(self) -> Dict[str, str]:
        """Prepare environment variables for the Cloud Run service.

        Returns:
            Dictionary of environment variables.
        """
        # Use IP addresses if provided, otherwise fall back to URLs
        bus_host = self._bus_url
        redis_host = self._redis_url

        env_vars = {
            # Bus configuration
            "UNIVERSE": str(self._scan_id),
            "MQ_SERVICE_HOST": bus_host,
            "MQ_VHOST": self._bus_vhost,
            "MQ_EXCHANGE_TOPIC": self._bus_exchange_topic,
            # Redis configuration
            "REDIS_URL": self._redis_url,  # Full URL for backward compatibility
            "REDIS_HOST": redis_host,  # IP or hostname for direct access
            # Agent configuration
            "AGENT_KEY": self._agent_settings.key,
            "AGENT_ARGS": str(self._agent_settings.args)
            if self._agent_settings.args
            else "",
            "AGENT_HEALTHCHECK_HOST": "0.0.0.0",
            "AGENT_HEALTHCHECK_PORT": "5000",
        }

        # Add agent-specific arguments as individual env vars
        if self._agent_settings.args:
            for arg_key, arg_value in self._agent_settings.args.items():
                env_vars[f"AGENT_ARG_{arg_key.upper()}"] = str(arg_value)

        # Add optional configuration
        if self._tracing_collector_url:
            env_vars["TRACE_COLLECTOR_URL"] = self._tracing_collector_url

        # Add Redis max connections if configured
        if self._agent_settings.redis_max_connections is not None:
            env_vars["REDIS_MAX_CONNECTIONS"] = str(
                self._agent_settings.redis_max_connections
            )

        return env_vars

    def _get_resource_limits(self) -> Dict[str, Any]:
        """Get resource limits based on agent configuration.

        Returns:
            Dictionary with resource configuration.
        """
        # Default Cloud Run configuration
        resources = {
            "memory": "512Mi",  # Default 512MB
            "cpu": "1",  # Default 1 CPU
        }

        # TODO: Parse agent definition for resource requirements
        # For now, use defaults - could be enhanced to read from agent schema

        return resources

    def _create_job_request(self, scan_id: int) -> run_v2.CreateJobRequest:
        """Create a Cloud Run job request.

        Args:
            scan_id: Scan ID for resource labeling.

        Returns:
            Create job request.
        """
        # Prepare environment variables
        env_vars_dict = self._prepare_environment_variables()
        env_vars = [
            run_v2.EnvVar(name=key, value=value) for key, value in env_vars_dict.items()
        ]

        # Get resource limits
        resources = self._get_resource_limits()

        # Create container configuration
        container = run_v2.Container(
            image=self._agent_settings.container_image,
            env=env_vars,
            resources=run_v2.ResourceRequirements(
                limits={
                    "memory": resources["memory"],
                    "cpu": resources["cpu"],
                }
            ),
            ports=[run_v2.ContainerPort(container_port=5000)],
        )

        # Create job configuration (single instance, manual scaling)
        job = run_v2.Job(
            template=run_v2.ExecutionTemplate(
                template=run_v2.TaskTemplate(
                    containers=[container],
                    max_retries=0,
                    timeout=None,  # No timeout for long-running processes
                    service_account=self._gcp_service_account or None,
                ),
                labels={
                    "ostorlab-scan-id": str(scan_id),
                    "ostorlab-agent-key": self._agent_settings.key,
                    "ostorlab-runtime": self._runtime_name,
                },
                annotations={
                    # Start with 1 instance and keep manual control (no autoscaling bursts)
                    "run.googleapis.com/launch-stage": launch_stage_pb2.LaunchStage.BETA,
                    "run.googleapis.com/priority": "DEFAULT",
                },
            ),
            metadata=run_v2.JobMetaData(
                name=self._service_name,
                labels={
                    "ostorlab-managed": "true",
                    "ostorlab-scan-id": str(scan_id),
                },
            ),
        )

        # Configure manual scaling: 1 task, 1 instance
        job.template.task_count = 1
        job.template.parallelism = 1

        # Create the request
        parent = f"projects/{self._gcp_project_id}/locations/{self._gcp_region}"

        return run_v2.CreateJobRequest(
            parent=parent,
            job=job,
            job_id=self._service_name,
        )

    def deploy_service(self, scan_id: int) -> str:
        """Deploy the agent as a Cloud Run job and start one execution.

        Args:
            scan_id: Scan ID for resource labeling.

        Returns:
            The deployed job name.

        Raises:
            CloudRunError: If deployment fails.
        """
        logger.info(
            f"Deploying {self._agent_settings.key} as Cloud Run job {self._service_name}"
        )

        try:
            # Create job request
            request = self._create_job_request(scan_id)

            # Deploy job
            operation = self._client.create_job(request=request)
            operation.result(timeout=300)  # 5 minute timeout for creation

            # Start a single execution for the job
            run_parent = f"projects/{self._gcp_project_id}/locations/{self._gcp_region}/jobs/{self._service_name}"
            run_request = run_v2.RunJobRequest(name=run_parent)
            run_operation = self._client.run_job(request=run_request)
            run_operation.result(timeout=300)

            logger.info(f"Successfully deployed and started job {self._service_name}")

            return self._service_name

        except Exception as e:
            logger.error(f"Failed to deploy job {self._service_name}: {e}")
            raise CloudRunError(
                f"Failed to deploy agent {self._agent_settings.key}: {e}"
            )

    def update_service(self) -> None:
        """Update the deployed Cloud Run job (environment variables)."""
        logger.info(f"Updating job {self._service_name}")

        try:
            job_path = f"projects/{self._gcp_project_id}/locations/{self._gcp_region}/jobs/{self._service_name}"
            job = self._client.get_job(name=job_path)

            env_vars_dict = self._prepare_environment_variables()
            job.template.template.containers[0].env = [
                run_v2.EnvVar(name=key, value=value)
                for key, value in env_vars_dict.items()
            ]

            request = run_v2.UpdateJobRequest(job=job)
            operation = self._client.update_job(request=request)
            operation.result(timeout=300)

            logger.info(f"Successfully updated job {self._service_name}")

        except Exception as e:
            logger.error(f"Failed to update job {self._service_name}: {e}")
            raise CloudRunError(f"Failed to update job: {e}")

    def delete_service(self) -> None:
        """Delete the Cloud Run job."""
        logger.info(f"Deleting job {self._service_name}")

        try:
            job_path = f"projects/{self._gcp_project_id}/locations/{self._gcp_region}/jobs/{self._service_name}"
            operation = self._client.delete_job(name=job_path)
            operation.result(timeout=300)
            logger.info(f"Successfully deleted job {self._service_name}")

        except Exception as e:
            logger.error(f"Failed to delete job {self._service_name}: {e}")
            raise CloudRunError(f"Failed to delete job: {e}")

    def get_service_status(self) -> Dict[str, Any]:
        """Get the status of the deployed job and its latest execution."""
        try:
            job_path = f"projects/{self._gcp_project_id}/locations/{self._gcp_region}/jobs/{self._service_name}"
            job = self._client.get_job(name=job_path)

            execution_info = None
            if job.latest_created_execution:
                execution = self._executions_client.get_execution(
                    name=job.latest_created_execution
                )
                execution_info = {
                    "name": execution.name,
                    "state": execution.state,
                    "conditions": execution.conditions,
                    "start_time": execution.create_time,
                    "completion_time": execution.completion_time,
                }

            return {
                "name": job.name,
                "latest_execution": execution_info,
                "observed_generation": job.observed_generation,
            }

        except Exception as e:
            logger.error(f"Failed to get status for {self._service_name}: {e}")
            raise CloudRunError(f"Failed to get job status: {e}")

    def is_healthy(self) -> bool:
        """Check if the latest execution of the job succeeded."""
        try:
            status = self.get_service_status()
            execution = status.get("latest_execution")
            if execution is None:
                return False

            return execution.get("state") == run_v2.Execution.State.SUCCEEDED

        except Exception as e:
            logger.error(f"Failed to check health for {self._service_name}: {e}")
            return False
