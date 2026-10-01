"""Tests for CLI agent delete command."""

import docker
from click import testing
from pytest_mock import plugin

from ostorlab.cli import rootcli


def testAgentDeleteCLI_always_listDockerImagesWithAgent(
    mocker: plugin.MockerFixture, offline_docker_client: docker.DockerClient
) -> None:
    """Test oxo agent delete CLI command.

    This is just a smoke test to avoid a complex mock.
    """
    image_list_mock = mocker.patch(
        "docker.models.images.ImageCollection.list", return_value=[]
    )

    runner = testing.CliRunner()

    result = runner.invoke(
        rootcli.rootcli, ["agent", "delete", "agent/ostorlab/big_fuzzer"]
    )

    assert "ERROR" in result.output
    image_list_mock.assert_called_once()
