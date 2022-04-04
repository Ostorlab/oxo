"""Redis service in charge of providing capabilities like QPS limiting, distributed locking and distributed storage."""
import logging
from typing import Dict

import docker
import tenacity
from docker import errors
from docker import types
from docker.models import services

logger = logging.getLogger(__name__)

REDIS_IMAGE = 'redis:latest'


class LocalRedis:
    """Redis service spawned a docker swarm service."""

    def __init__(self,
                 name: str,
                 network: str,
                 exposed_ports: Dict[int, int] = None,
                 image: str = REDIS_IMAGE) -> None:
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
        self._redis_host = f'redis_{self._name}'
        # service
        self._redis_service = None
        # exposed_port
        self._exposed_ports = exposed_ports

    @property
    def url(self) -> str:
        """URL to connect to the local Redis instance."""
        return f'redis://{self._redis_host}:6379/'

    @property
    def service(self):
        return self._redis_service

    def start(self) -> None:
        """Start local Redis instance."""
        self._create_network()
        self._redis_service = self._start_redis()

        if self._redis_service is not None and not self._is_service_healthy():
            logger.error('Redis container for service %s is not ready', self._redis_service.id)
            return

    def stop(self):
        """Stop the local Redis instance."""
        for service in self._docker_client.services.list():
            universe = service.attrs['Spec']['Labels'].get('ostorlab.universe')
            if universe is not None and service.name.startswith('redis_') and self._name in universe:
                service.remove()

    def _create_network(self):
        if any(network.name == self._network for network in self._docker_client.networks.list()):
            logger.warning('network already exists.')
        else:
            logger.info('creating private network %s', self._network)
            return self._docker_client.networks.create(
                name=self._network,
                driver='overlay',
                attachable=True,
                labels={'ostorlab.universe': self._name},
                check_duplicate=True
            )

    def _start_redis(self) -> services.Service:
        try:
            logger.info('starting Redis')
            endpoint_spec = types.services.EndpointSpec(mode='vip', ports=self._exposed_ports)
            service_mode = types.services.ServiceMode('replicated', replicas=1)
            return self._docker_client.services.create(
                image=self._redis_image,
                networks=[self._network],
                name=self._redis_host,
                restart_policy=types.RestartPolicy(condition='any'),
                mode=service_mode,
                labels={'ostorlab.universe': self._name, 'ostorlab.redis': ''},
                endpoint_spec=endpoint_spec)
        except docker.errors.APIError as e:
            error_message = f'Redis service could not be started. Reason: {e}.'
            logger.error(error_message)
            return

    @tenacity.retry(stop=tenacity.stop_after_attempt(20),
                    wait=tenacity.wait_exponential(multiplier=1, max=12),
                    # return last value and don't raise RetryError exception.
                    retry_error_callback=lambda lv: lv.outcome.result(),
                    retry=tenacity.retry_if_result(lambda v: v is False))
    def _is_service_healthy(self) -> bool:
        logger.info('checking service %s', self._redis_service.name)
        return self.is_healthy

    @property
    def is_healthy(self) -> bool:
        try:
            return self._redis_service is not None and \
                   len([task for task in self._redis_service.tasks() if task['Status']['State'] == 'running']) == 1
        except errors.DockerException:
            return False
