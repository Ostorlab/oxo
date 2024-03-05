"""Jaeger service to collect Agent traces."""

import logging
from typing import Dict, Optional

import docker
import tenacity
from docker import errors
from docker import types
from docker.models import services

logger = logging.getLogger(__name__)

JAEGER_IMAGE = "jaegertracing/all-in-one:latest"
DEFAULT_EXPOSED_PORTS = {
    5775: 5775,
    6831: 6831,
    6832: 6832,
    5778: 5778,
    16686: 16686,
    14268: 14268,
    9411: 9411,
}
DEFAULT_JAEGER_PORT = 6831
DEFAULT_JAEGER_UI_PORT = 16686


class LocalJaeger:
    """Jaeger service spawned a docker swarm service."""

    def __init__(
        self,
        name: str,
        network: str,
        exposed_ports: Dict[int, int] = None,
        image: str = JAEGER_IMAGE,
    ) -> None:
        """Initialize the Jaeger service parameters.
        Args:
            name: Name of the service.
            network: Network used for the Docker Jaeger service.
            exposed_ports: The list of Jaeger service exposed ports
            image: Jaeger Docker image
        """
        self._name = name
        self._docker_client = docker.from_env()
        # images
        self._jaeger_image = image
        self._network = network
        self._jaeger_host = f"jaeger_{self._name}"
        # service
        self._jaeger_service = None
        # exposed_port
        self._exposed_ports = exposed_ports or DEFAULT_EXPOSED_PORTS

    @property
    def url(self) -> str:
        """URL to connect to the local Jaeger instance."""
        return f"jaeger://{self._jaeger_host}:{DEFAULT_JAEGER_PORT}"

    @property
    def management_interface_ui(self) -> str:
        """URL to management user interface of the Jaeger instance."""
        return f"http://127.0.0.1:{DEFAULT_JAEGER_UI_PORT}"

    @property
    def service(self):
        return self._jaeger_service

    def start(self) -> None:
        """Start local Jaeger instance."""
        self._create_network()
        self._jaeger_service = self._start_jaeger()

    def stop(self):
        """Stop the local Jaeger instance."""
        for service in self._docker_client.services.list():
            universe = service.attrs["Spec"]["Labels"].get("ostorlab.universe")
            if (
                universe is not None
                and service.name.startswith("jaeger_")
                and self._name in universe
            ):
                service.remove()

    def _create_network(self):
        if any(
            network.name == self._network
            for network in self._docker_client.networks.list()
        ):
            logger.warning("network already exists.")
        else:
            logger.info("creating private network %s", self._network)
            return self._docker_client.networks.create(
                name=self._network,
                driver="overlay",
                attachable=True,
                labels={"ostorlab.universe": self._name},
                check_duplicate=True,
            )

    def _start_jaeger(self) -> Optional[services.Service]:
        try:
            logger.info("starting Jaeger")
            endpoint_spec = types.services.EndpointSpec(
                mode="vip", ports=self._exposed_ports
            )
            service_mode = types.services.ServiceMode("replicated", replicas=1)
            return self._docker_client.services.create(
                image=self._jaeger_image,
                networks=[self._network],
                name=self._jaeger_host,
                restart_policy=types.RestartPolicy(condition="any"),
                mode=service_mode,
                labels={"ostorlab.universe": self._name, "ostorlab.jaeger": ""},
                endpoint_spec=endpoint_spec,
            )
        except docker.errors.APIError as e:
            error_message = f"Jaeger service could not be started. Reason: {e}."
            logger.error(error_message)
            return

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(20),
        wait=tenacity.wait_fixed(0.5),
        # return last value and don't raise RetryError exception.
        retry_error_callback=lambda lv: lv.outcome,
        retry=tenacity.retry_if_result(lambda v: v is False),
    )
    def is_service_healthy(self) -> bool:
        logger.info("checking service %s", self._jaeger_service.name)
        return self.is_healthy

    @property
    def is_healthy(self) -> bool:
        try:
            return (
                self._jaeger_service is not None
                and len(
                    [
                        task
                        for task in self._jaeger_service.tasks()
                        if task["Status"]["State"] == "running"
                    ]
                )
                == 1
            )
        except errors.DockerException:
            return False
