"""Tests for agent_fetcher module."""

from unittest.mock import Mock, patch

from ostorlab.cli import agent_fetcher


def testGetContainerImage_whenExactVersionRequested_shouldReturnExactMatch() -> None:
    """Test that version matching is exact, not regex-based."""
    with patch("ostorlab.cli.agent_fetcher.docker.from_env") as mock_docker:
        mock_client = Mock()
        mock_docker.return_value = mock_client
        mock_img = Mock()
        mock_img.tags = ["agent_ostorlab_nmap:v1.0.1", "agent_ostorlab_nmap:v1.0.0"]
        mock_client.images.list.return_value = [mock_img]

        result = agent_fetcher.get_container_image("agent/ostorlab/nmap", "1.0.0")

        assert result == "agent_ostorlab_nmap:v1.0.0"


def testGetContainerImage_whenVersionNotFound_shouldReturnNone() -> None:
    """Test behavior when specified version is not found locally."""
    with patch("ostorlab.cli.agent_fetcher.docker.from_env") as mock_docker:
        mock_client = Mock()
        mock_docker.return_value = mock_client

        mock_img = Mock()
        mock_img.tags = ["agent_ostorlab_nmap:v0.2.0"]
        mock_client.images.list.return_value = [mock_img]

        result = agent_fetcher.get_container_image("agent/ostorlab/nmap", "0.1.0")

        assert result is None


def testGetContainerImage_whenNoVersionProvided_shouldReturnLatest() -> None:
    """Test that when no version specified, returns latest available."""
    with patch("ostorlab.cli.agent_fetcher.docker.from_env") as mock_docker:
        mock_client = Mock()
        mock_docker.return_value = mock_client
        mock_img = Mock()
        mock_img.tags = ["agent_ostorlab_nmap:v0.1.0", "agent_ostorlab_nmap:v0.2.0"]
        mock_client.images.list.return_value = [mock_img]

        result = agent_fetcher.get_container_image("agent/ostorlab/nmap", None)

        assert result == "agent_ostorlab_nmap:v0.2.0"


@patch("ostorlab.cli.agent_fetcher.get_container_image")
def testGetDefinition_whenVersionParameterProvided_shouldCallGetContainerImageWithVersion(
    mock_get_container_image,
) -> None:
    """Test that get_definition passes version parameter to get_container_image."""
    mock_get_container_image.return_value = "agent_ostorlab_nmap:v0.1.0"

    with patch("ostorlab.cli.agent_fetcher.docker.from_env") as mock_docker:
        mock_client = Mock()
        mock_docker.return_value = mock_client

        mock_docker_image = Mock()
        mock_docker_image.labels.get.return_value = "kind: Agent\nname: nmap"
        mock_client.images.get.return_value = mock_docker_image

        with patch(
            "ostorlab.agent.definitions.AgentDefinition.from_yaml"
        ) as mock_from_yaml:
            mock_definition = Mock()
            mock_from_yaml.return_value = mock_definition

            result = agent_fetcher.get_definition(
                "agent/ostorlab/nmap", version="v0.1.0"
            )

            mock_get_container_image.assert_called_once_with(
                agent_key="agent/ostorlab/nmap", version="v0.1.0"
            )
            assert result == mock_definition


@patch("ostorlab.cli.agent_fetcher.get_container_image")
def testGetDefinition_whenNoVersionProvided_shouldCallGetContainerImageWithNone(
    mock_get_container_image,
) -> None:
    """Test that get_definition works without version parameter."""
    mock_get_container_image.return_value = "agent_ostorlab_nmap:latest"

    with patch("ostorlab.cli.agent_fetcher.docker.from_env") as mock_docker:
        mock_client = Mock()
        mock_docker.return_value = mock_client

        mock_docker_image = Mock()
        mock_docker_image.labels.get.return_value = "kind: Agent\nname: nmap"
        mock_client.images.get.return_value = mock_docker_image

        with patch(
            "ostorlab.agent.definitions.AgentDefinition.from_yaml"
        ) as mock_from_yaml:
            mock_definition = Mock()
            mock_from_yaml.return_value = mock_definition

            result = agent_fetcher.get_definition("agent/ostorlab/nmap")

            mock_get_container_image.assert_called_once_with(
                agent_key="agent/ostorlab/nmap", version=None
            )
            assert result == mock_definition
