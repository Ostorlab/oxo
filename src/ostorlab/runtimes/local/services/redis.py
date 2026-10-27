"""Redis service in charge of providing capabilities like QPS limiting, distributed locking and distributed storage."""

from __future__ import annotations

import logging
import typing

import docker
import tenacity
from docker import errors
from docker import types
from docker.models import networks
from docker.models import services

from ostorlab.runtimes.local import resources
from ostorlab.runtimes.local import snapshot
from ostorlab.runtimes.local.services import container_exec

logger = logging.getLogger(__name__)

REDIS_IMAGE = "redis:latest"
REDIS_READINESS_COMMAND = ["redis-cli", "ping"]
REDIS_READINESS_ATTEMPTS = 60
REDIS_READINESS_WAIT_SECONDS = 1
REDIS_RESTORE_FILE = "ostorlab_redis_restore.resp"


class LocalRedis:
    """Redis service spawned a docker swarm service."""

    def __init__(
        self,
        name: int | str,
        network: str,
        exposed_ports: typing.Optional[dict[int, int]] = None,
        image: str = REDIS_IMAGE,
    ) -> None:
        """Initialize the Redis service parameters.
        Args:
            name: Name of the service.
            network: Network used for the Docker Redis service.
            exposed_ports: The list of Redis service exposed ports
            image: Redis Docker image
        """
        self._name = name
        self._docker_client = docker.from_env()
        # images
        self._redis_image = image
        self._network = network
        self._redis_host = f"redis_{self._name}"
        # service
        self._redis_service: typing.Optional[services.Service] = None
        # exposed_port
        self._exposed_ports = exposed_ports

    @property
    def url(self) -> str:
        """URL to connect to the local Redis instance."""
        return f"redis://{self._redis_host}:6379/"

    @property
    def service(self) -> typing.Optional[services.Service]:
        return self._redis_service

    def start(self) -> None:
        """Start local Redis instance."""
        self._create_network()
        self._redis_service = self._start_redis()

    def stop(self) -> None:
        """Stop the local Redis instance."""
        for service in self._docker_client.services.list():
            universe = service.attrs["Spec"]["Labels"].get("ostorlab.universe")
            if (
                universe is not None
                and service.name.startswith("redis_")
                and self._name in universe
            ):
                typing.cast(typing.Callable[[], None], service.remove)()

    def _create_network(self) -> typing.Optional[networks.Network]:
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
        return None

    def _start_redis(self) -> typing.Optional[services.Service]:
        try:
            logger.info("starting Redis")
            endpoint_spec = typing.cast(
                typing.Callable[..., types.services.EndpointSpec],
                types.services.EndpointSpec,
            )(mode="vip", ports=self._exposed_ports)
            service_mode = types.services.ServiceMode("replicated", replicas=1)
            return typing.cast(
                typing.Callable[..., services.Service],
                self._docker_client.services.create,
            )(
                image=self._redis_image,
                networks=[self._network],
                name=self._redis_host,
                restart_policy=types.RestartPolicy(condition="any"),
                mode=service_mode,
                labels={"ostorlab.universe": self._name, "ostorlab.redis": ""},
                endpoint_spec=endpoint_spec,
                resources=resources.swarm_resources(resources.memory_limit("redis")),
            )
        except docker.errors.APIError as e:
            error_message = f"Redis service could not be started. Reason: {e}."
            logger.error(error_message)
            return None

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(20),
        wait=tenacity.wait_fixed(0.5),
        retry_error_callback=lambda _: False,
        retry=tenacity.retry_if_result(lambda v: v is False),
    )
    def is_service_healthy(self) -> bool:
        logger.info(
            "checking service %s",
            typing.cast(services.Service, self._redis_service).name,
        )
        return self.is_healthy

    @property
    def is_healthy(self) -> bool:
        try:
            return (
                self._redis_service is not None
                and len(
                    [
                        task
                        for task in typing.cast(
                            typing.Callable[[], list[dict[str, typing.Any]]],
                            self._redis_service.tasks,
                        )()
                        if task["Status"]["State"] == "running"
                    ]
                )
                == 1
            )
        except errors.DockerException:
            return False

    def restore(self, keys: typing.Sequence[snapshot.RedisKey]) -> None:
        """Restore the keys of a paused universe, before its agents start.

        The `RESTORE` commands are copied to the Redis container and sent with `redis-cli --pipe` from inside it.

        Args:
            keys: The keys to restore, existing keys are replaced.

        Raises:
            container_exec.ExecError: When Redis is not ready or a key cannot be restored.
        """
        if len(keys) == 0:
            return
        self._wait_accepting_connections()
        commands = b"".join(
            _redis_command(
                b"RESTORE", key.key, str(key.ttl_ms).encode(), key.value, b"REPLACE"
            )
            for key in keys
        )
        path = f"{container_exec.FILES_DIRECTORY}/{REDIS_RESTORE_FILE}"
        # `redis-cli --pipe` exits with an error when a command fails, the file is removed either way.
        container_exec.run(
            self._docker_client,
            self._redis_service,
            [
                "sh",
                "-c",
                f"redis-cli --pipe < {path}; status=$?; rm -f {path}; exit $status",
            ],
            files={REDIS_RESTORE_FILE: commands},
        )
        logger.info("restored %s redis keys", len(keys))

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(REDIS_READINESS_ATTEMPTS),
        wait=tenacity.wait_fixed(REDIS_READINESS_WAIT_SECONDS),
        retry=tenacity.retry_if_exception_type(container_exec.ExecError),
        reraise=True,
    )
    def _wait_accepting_connections(self) -> None:
        """Wait for Redis to answer, a running task only means its container started."""
        output = container_exec.run(
            self._docker_client, self._redis_service, REDIS_READINESS_COMMAND
        )
        if output.strip() != b"PONG":
            raise container_exec.ExecError(f"redis is not ready: {output!r}")


def _redis_command(*parts: bytes) -> bytes:
    """Encode a command in the Redis protocol, the format `redis-cli --pipe` reads."""
    return f"*{len(parts)}\r\n".encode() + b"".join(
        f"${len(part)}\r\n".encode() + part + b"\r\n" for part in parts
    )
