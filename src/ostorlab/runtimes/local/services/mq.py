"""RabbitMQ service in charge of routing Agent messages."""

import binascii
import hashlib
import logging
import os
import pathlib
import uuid
from typing import Dict

import docker
import tenacity
from docker import errors
from docker import types
from docker.models import services

logger = logging.getLogger(__name__)

MQ_IMAGE = "rabbitmq:3.9-management"
MQ_ADVANCED_CONF_PATH = "/etc/rabbitmq/advanced.config"


class LocalRabbitMQ:
    """RabbitMQ service spawned a docker swarm service."""

    def __init__(
        self,
        name: str,
        network: str,
        exposed_ports: Dict[int, int] = None,
        image: str = MQ_IMAGE,
    ) -> None:
        """Initialize the MQ service parameters.
        Args:
            name: Name of the service.
            network: Network used for the Docker MQ service.
            exposed_ports: The list of MQ service exposed ports
            image: MQ Docker image
        """
        self._uuid = uuid.uuid4()
        self._name = name
        self._docker_client = docker.from_env()
        # images
        self._mq_image = image
        self._network = network
        self._mq_host = f"mq_{self._name}"
        # service
        self._mq_service = None
        # exposed_port
        self._exposed_ports = exposed_ports

    @property
    def url(self) -> str:
        """URL to connect to the local RabbitMQ instance."""
        return f"amqp://guest:guest@{self._mq_host}:5672/"

    @property
    def vhost(self):
        """Default vhost."""
        return "/"

    @property
    def service(self):
        """The RabbitMQ corresponding docker service."""
        return self._mq_service

    @property
    def management_url(self) -> str:
        """URL to connect to the management interface of the RabbitMQ instance."""
        return f"http://guest:guest@{self._mq_host}:15672/"

    def start(self) -> None:
        """Start local Rabbit MQ instance."""
        self._create_network()
        self._mq_service = self._start_mq()

    def stop(self):
        """Stop local Rabiit MQ instance."""
        for service in self._docker_client.services.list():
            universe = service.attrs["Spec"]["Labels"].get("ostorlab.universe")
            if (
                universe is not None
                and service.name.startswith("mq_")
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

    def _create_mq_advanced_config(self) -> types.services.ConfigReference:
        conf_path = (
            pathlib.Path(__file__).parent / "configurations/mq_advanced_conf.config"
        )
        with open(conf_path, "rb") as conf_file:
            mq_advanced_configuration = conf_file.read()
        config_name = hashlib.md5(
            f"mq_advanced_config_{self._name}_{self._uuid}".encode()
        ).hexdigest()

        try:
            mq_advanced_config = self._docker_client.configs.get(config_name)
            logging.warning(
                "found existing config %s, config will removed", config_name
            )
            mq_advanced_config.remove()
        except docker.errors.NotFound:
            logging.debug("all good, config %s is new", config_name)

        docker_config = self._docker_client.configs.create(
            name=config_name,
            labels={
                "ostorlab.universe": self._name,
                "ostorlab.mq.advanced.config": "true",
            },
            data=mq_advanced_configuration,
        )
        return types.services.ConfigReference(
            config_id=docker_config.id,
            config_name=config_name,
            filename=MQ_ADVANCED_CONF_PATH,
        )

    def _start_mq(self) -> services.Service:
        try:
            logger.info("starting MQ")
            endpoint_spec = types.services.EndpointSpec(
                mode="vip", ports=self._exposed_ports
            )
            service_mode = types.services.ServiceMode("replicated", replicas=1)
            mq_advanced_configuration = self._create_mq_advanced_config()
            configs = [mq_advanced_configuration]
            persistent_storage = docker.types.Mount(
                target="/var/lib/rabbitmq", source=f"{self._name}_mq_data"
            )
            return self._docker_client.services.create(
                image=self._mq_image,
                networks=[self._network],
                hostname="mq",
                name=self._mq_host,
                env=[
                    "TASK_ID={{.Task.Slot}}",
                    f"MQ_SERVICE_NAME={self._mq_host}",
                    f"RABBITMQ_ERLANG_COOKIE={binascii.hexlify(os.urandom(10)).decode()}",
                ],
                restart_policy=types.RestartPolicy(condition="any"),
                mode=service_mode,
                labels={"ostorlab.universe": self._name, "ostorlab.mq": ""},
                configs=configs,
                endpoint_spec=endpoint_spec,
                mounts=[persistent_storage],
            )
        except docker.errors.APIError as e:
            error_message = f"MQ service could not be started. Reason: {e}."
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
        logger.info("checking service %s", self._mq_service.name)
        return self.is_healthy

    @property
    def is_healthy(self) -> bool:
        """Check if the local Rabbit MQ instance is healthy.

        Returns:
            True if the instance is healthy, False otherwise.
        """
        try:
            return (
                self._mq_service is not None
                and len(
                    [
                        task
                        for task in self._mq_service.tasks()
                        if task["Status"]["State"] == "running"
                    ]
                )
                == 1
            )
        except errors.DockerException:
            return False
