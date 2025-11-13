"""Stream logs of a service from a thread."""

import threading
import time

import docker.errors
from docker.models import services as docker_service

from ostorlab.cli import console as cli_console


console = cli_console.Console()

COLOR_POOL = [
    "dodger_blue2",
    "deep_sky_blue3",
    "deep_sky_blue2",
    "cyan3",
    "spring_green2",
    "spring_green2",
    "grey37",
    "chartreuse4",
    "cornflower_blue",
    "chartreuse3",
    "steel_blue1",
    "dark_red",
    "plum4",
]


class _ServiceLogStream:
    """Stream logs from a specific docker service."""

    def __init__(self, service: docker_service.Service, color: str) -> None:
        self._service: docker_service.Service = service
        self._color: str = color
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Starts the service log stream, in the background."""
        self._thread = threading.Thread(target=self._stream, daemon=True)
        self._thread.start()

    def _stream(self) -> None:
        logs = self._service.logs(details=False, follow=True, stdout=True, stderr=True)
        name = self._service.name
        for line in logs:
            if self._stop_event.is_set():
                break
            console.info(f"[{self._color} bold]{name}:[/] {line[:-1].decode()}")

    def stop(self) -> None:
        """Stop the log stream."""
        if self._thread is None:
            return
        self._stop_event.set()
        # thread may check the stop event late when the thread calling LogStream.wait has already exited
        # so we join the thread with a timeout.
        self._thread.join(timeout=1)


class LogStream:
    """Docker service log streamer."""

    def __init__(self, docker_client: docker.DockerClient) -> None:
        self._color_map: dict[str, str] = {}
        self._log_streams: dict[str, _ServiceLogStream] = {}
        self._docker_client = docker_client

    def stream(self, service: docker_service.Service) -> None:
        """
        Stream logs of a service without blocking.

        Args:
            service: Docker service.
        """
        color = self._select_color(service)
        service_id = service.id

        if service_id in self._log_streams:
            return

        log_streamer = _ServiceLogStream(service, color=color)
        self._log_streams[service_id] = log_streamer
        log_streamer.start()

    def wait(self) -> None:
        """Wait for all streams to finish."""
        # The logs generator returned by the docker sdk does not return when the service is removed.
        # So we need to loop and poll each service to stop the stream manually. Thank you Docker.
        while len(self._log_streams) > 0:
            for service_id, log_stream in list(self._log_streams.items()):
                if self._service_exists(service_id) is False:
                    log_stream.stop()
                    del self._log_streams[service_id]
            time.sleep(1)

    def _select_color(self, service):
        """Select color for console output of service."""
        if service.name in self._color_map:
            color = self._color_map[service.name]
        else:
            # To avoid running out of colors, we insert them back.
            color = COLOR_POOL.pop()
            COLOR_POOL.insert(0, color)
        return color

    def _service_exists(self, service_id) -> bool:
        try:
            self._docker_client.services.get(service_id)
            return True
        except docker.errors.NotFound:
            return False
