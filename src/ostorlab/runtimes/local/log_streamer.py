"""Stream logs of a service from a thread."""

import threading
from typing import Generator

import docker.models.services

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


def _stream_log(
    log_generator: Generator[bytes, None, None], name: str, color: str
) -> None:
    """Collect log from log generator and format them using the console API."""
    for line in log_generator:
        console.info(f"[{color} bold]{name}:[/] {line[:-1].decode()}")


class LogStream:
    """Docker service log streamer."""

    def __init__(self):
        self._threads = []
        self._color_map = {}

    def stream(self, service: docker.models.services.Service) -> None:
        """Stream logs of a service without blocking.

        Implementation spawns a dedicated deamon thread.

        Args:
            service: Docker service.
        """
        color = self._select_color(service)
        logs = service.logs(details=False, follow=True, stdout=True, stderr=True)
        t = threading.Thread(
            target=_stream_log, args=(logs, service.name, color), daemon=False
        )
        self._threads.append(t)
        t.start()

    def _select_color(self, service):
        """Select color for console output of service."""
        if service.name in self._color_map:
            color = self._color_map[service.name]
        else:
            # To avoid running out of colors, we insert them back.
            color = COLOR_POOL.pop()
            COLOR_POOL.insert(0, color)
        return color
