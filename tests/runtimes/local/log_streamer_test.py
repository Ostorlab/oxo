"""Unittest for the log streamer."""

from unittest import mock

import docker
import pytest
from docker.models import services as services_model
from pytest_mock import plugin

from ostorlab.runtimes.local import log_streamer


@pytest.fixture()
def service_mock(mocker: plugin.MockerFixture) -> mock.MagicMock:
    """Creates a mock of a docker service."""
    service_mock = mocker.MagicMock(spec=services_model.Service)
    service_mock.id = "service_id"
    service_mock.name = "service_name"
    service_mock.logs.return_value = [b"log1\n", b"log2\n"]
    return service_mock


def testServiceLogStream_whenLogsAreAvailable_logsArePrintedToConsole(
    mocker: plugin.MockerFixture, service_mock: mock.MagicMock
) -> None:
    """Test that logs are printed to the console."""
    console_mock = mocker.patch("ostorlab.runtimes.local.log_streamer.console")
    mocker.patch("threading.Event.is_set", side_effect=[False, False, True])

    stream = log_streamer._ServiceLogStream(service_mock, color="red")
    stream._stream()

    assert console_mock.info.call_count == 2
    console_mock.info.assert_has_calls(
        [
            mock.call("[red bold]service_name:[/] log1"),
            mock.call("[red bold]service_name:[/] log2"),
        ]
    )


def testLogStream_whenStreamIsCalled_aNewThreadIsStarted(
    mocker: plugin.MockerFixture, service_mock: mock.MagicMock
) -> None:
    """Test that a new thread is started when stream is called."""
    docker_client_mock = mocker.MagicMock(spec=docker.DockerClient)
    thread_mock = mocker.patch("threading.Thread")

    streamer = log_streamer.LogStream(docker_client_mock)
    streamer.stream(service_mock)

    thread_mock.assert_called_once()
    thread_mock.return_value.start.assert_called_once()


def testLogStream_whenStreamIsCalledTwice_onlyOneThreadIsStarted(
    mocker: plugin.MockerFixture, service_mock: mock.MagicMock
) -> None:
    """Test that calling stream twice for the same service does not start a new thread."""
    docker_client_mock = mocker.MagicMock(spec=docker.DockerClient)
    thread_mock = mocker.patch("threading.Thread")

    streamer = log_streamer.LogStream(docker_client_mock)
    streamer.stream(service_mock)
    streamer.stream(service_mock)

    thread_mock.assert_called_once()
    thread_mock.return_value.start.assert_called_once()


def testLogStreamWait_whenServiceIsRemoved_stopsTheStream(
    mocker: plugin.MockerFixture, service_mock: mock.MagicMock
) -> None:
    """Test that wait stops the stream when the service is removed."""
    docker_client_mock = mocker.MagicMock(spec=docker.DockerClient)
    mocker.patch("threading.Thread")
    mocker.patch("time.sleep")

    streamer = log_streamer.LogStream(docker_client_mock)
    streamer.stream(service_mock)

    docker_client_mock.services.get.side_effect = docker.errors.NotFound("not found")
    stop_mock = mocker.patch.object(log_streamer._ServiceLogStream, "stop")

    streamer.wait()

    stop_mock.assert_called_once()
    assert "service_id" not in streamer._log_streams


def testServiceLogStreamStop_whenCalled_setsStopEvent(
    mocker: plugin.MockerFixture, service_mock: mock.MagicMock
) -> None:
    """Test that stop sets the stop event."""
    stream = log_streamer._ServiceLogStream(service_mock, color="red")
    mocker.patch("threading.Thread")
    stream.start()

    stop_event_set_mock = mocker.spy(stream._stop_event, "set")
    stream.stop()

    stop_event_set_mock.assert_called_once()


def testLogStreamWait_whenServiceStillExists_doesNotStopTheStream(
    mocker: plugin.MockerFixture, service_mock: mock.MagicMock
) -> None:
    """Test that wait does not stop the stream when the service still exists."""
    docker_client_mock = mocker.MagicMock(spec=docker.DockerClient)
    mocker.patch("threading.Thread")
    sleep_mock = mocker.patch("time.sleep")
    sleep_mock.side_effect = [None, StopIteration]

    streamer = log_streamer.LogStream(docker_client_mock)
    streamer.stream(service_mock)

    docker_client_mock.services.get.return_value = service_mock
    stop_mock = mocker.patch.object(log_streamer._ServiceLogStream, "stop")

    with pytest.raises(StopIteration):
        streamer.wait()

    stop_mock.assert_not_called()
    assert "service_id" in streamer._log_streams
