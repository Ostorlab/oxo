"""Unit tests for the log streamer module."""

from time import sleep

import docker.models.services
from docker import errors as docker_errors
from pytest_mock import plugin

from ostorlab.runtimes.local import log_streamer


def testLogStreamer_whenServiceDoesntExistAnyMore_thenPrintScanCompleted(
    mocker: plugin.MockerFixture, mock_docker_service: docker.models.services.Service
) -> None:
    """Test that the log streamer prints a message when the services of scan don't exist anymore."""
    log_strm = log_streamer.LogStream()
    success_mock = mocker.patch("ostorlab.console.Console.success")
    info_mock = mocker.patch("ostorlab.console.Console.info")
    mocker.patch(
        "docker.models.services.ServiceCollection.get",
        side_effect=docker_errors.NotFound(""),
    )

    log_strm.stream(mock_docker_service)
    sleep(1)

    assert info_mock.call_count == 2
    assert "Test log line" in info_mock.call_args_list[0][0][0]
    assert "Another log line" in info_mock.call_args_list[1][0][0]
    assert success_mock.call_count == 1
    assert success_mock.call_args[0][0] == "Scan completed."
