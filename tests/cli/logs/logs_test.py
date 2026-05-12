"""Tests for CLI logs command."""

from unittest import mock

from click import testing

from ostorlab.cli import rootcli


def testOstorlabLogsCLI_whenNoAgentProvided_showsErrorMessage():
    """Test oxo logs command without --agent shows error."""
    runner = testing.CliRunner()
    result = runner.invoke(rootcli.rootcli, ["logs"])
    assert "Missing option '--agent'" in result.output
    assert result.exit_code == 2


def testOstorlabLogsCLI_whenNoServicesFound_showsErrorMessage(mocker):
    """Test oxo logs command when no running services match the agent key."""
    mocker.patch(
        "ostorlab.cli.agent_fetcher.get_container_image",
        return_value="agent_ostorlab_nmap:v0.1.0",
    )
    mock_docker_client = mock.Mock()
    mock_docker_client.services.list.return_value = []
    mocker.patch("docker.from_env", return_value=mock_docker_client)

    runner = testing.CliRunner()
    result = runner.invoke(rootcli.rootcli, ["logs", "--agent=agent/ostorlab/nmap"])

    assert "No running services found for agent agent/ostorlab/nmap" in result.output
    assert result.exit_code == 1


def testOstorlabLogsCLI_whenServicesFound_streamsLogs(mocker):
    """Test oxo logs command streams logs for matching services."""
    mocker.patch(
        "ostorlab.cli.agent_fetcher.get_container_image",
        return_value="agent_ostorlab_nmap:v0.1.0",
    )
    mock_service = mock.Mock()
    mock_service.attrs = {
        "Spec": {
            "TaskTemplate": {"ContainerSpec": {"Image": "agent_ostorlab_nmap:v0.1.0"}}
        }
    }
    mock_docker_client = mock.Mock()
    mock_docker_client.services.list.return_value = [mock_service]
    mocker.patch("docker.from_env", return_value=mock_docker_client)

    mock_log_stream = mocker.patch("ostorlab.runtimes.local.log_streamer.LogStream")
    mock_log_stream_instance = mock_log_stream.return_value
    mock_log_stream_instance.wait.side_effect = KeyboardInterrupt

    runner = testing.CliRunner()
    result = runner.invoke(rootcli.rootcli, ["logs", "--agent=agent/ostorlab/nmap"])

    assert mock_log_stream_instance.stream.called is True
    mock_log_stream_instance.stream.assert_called_once_with(mock_service)
    assert "Streaming logs for agent agent/ostorlab/nmap" in result.output


def testOstorlabLogsCLI_whenAgentImageNotInstalled_showsErrorMessage(mocker):
    """Test oxo logs command when agent image is not installed locally."""
    mocker.patch("ostorlab.cli.agent_fetcher.get_container_image", return_value=None)
    mock_docker_client = mock.Mock()
    mock_docker_client.services.list.return_value = []
    mocker.patch("docker.from_env", return_value=mock_docker_client)

    runner = testing.CliRunner()
    result = runner.invoke(rootcli.rootcli, ["logs", "--agent=agent/ostorlab/nmap"])

    assert "No running services found for agent agent/ostorlab/nmap" in result.output
    assert result.exit_code == 1


def testOstorlabLogsCLI_whenServiceImageHasDigest_matchesCorrectly(mocker):
    """Test that services with digest-based image references are matched."""
    mocker.patch(
        "ostorlab.cli.agent_fetcher.get_container_image",
        return_value="agent_ostorlab_nmap:v0.1.0",
    )
    mock_service = mock.Mock()
    mock_service.attrs = {
        "Spec": {
            "TaskTemplate": {
                "ContainerSpec": {
                    "Image": "agent_ostorlab_nmap:v0.1.0@sha256:abcdef123456"
                }
            }
        }
    }
    mock_docker_client = mock.Mock()
    mock_docker_client.services.list.return_value = [mock_service]
    mocker.patch("docker.from_env", return_value=mock_docker_client)

    mock_log_stream = mocker.patch("ostorlab.runtimes.local.log_streamer.LogStream")
    mock_log_stream_instance = mock_log_stream.return_value
    mock_log_stream_instance.wait.side_effect = KeyboardInterrupt

    runner = testing.CliRunner()
    _ = runner.invoke(rootcli.rootcli, ["logs", "--agent=agent/ostorlab/nmap"])

    assert mock_log_stream_instance.stream.called is True


def testOstorlabLogsCLI_whenMultipleServicesFound_streamsAllLogs(mocker):
    """Test oxo logs command streams logs for all matching services."""
    mocker.patch(
        "ostorlab.cli.agent_fetcher.get_container_image",
        return_value="agent_ostorlab_nmap:v0.1.0",
    )
    mock_service1 = mock.Mock()
    mock_service1.attrs = {
        "Spec": {
            "TaskTemplate": {"ContainerSpec": {"Image": "agent_ostorlab_nmap:v0.1.0"}}
        }
    }
    mock_service2 = mock.Mock()
    mock_service2.attrs = {
        "Spec": {
            "TaskTemplate": {"ContainerSpec": {"Image": "agent_ostorlab_nmap:v0.1.0"}}
        }
    }
    mock_docker_client = mock.Mock()
    mock_docker_client.services.list.return_value = [mock_service1, mock_service2]
    mocker.patch("docker.from_env", return_value=mock_docker_client)

    mock_log_stream = mocker.patch("ostorlab.runtimes.local.log_streamer.LogStream")
    mock_log_stream_instance = mock_log_stream.return_value
    mock_log_stream_instance.wait.side_effect = KeyboardInterrupt

    runner = testing.CliRunner()
    result = runner.invoke(rootcli.rootcli, ["logs", "--agent=agent/ostorlab/nmap"])

    assert mock_log_stream_instance.stream.call_count == 2
    mock_log_stream_instance.stream.assert_any_call(mock_service1)
    mock_log_stream_instance.stream.assert_any_call(mock_service2)
    assert "Streaming logs for agent agent/ostorlab/nmap" in result.output
