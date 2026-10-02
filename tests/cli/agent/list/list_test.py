"""Tests for CLI agent list command."""

from click import testing

from ostorlab.cli import rootcli


def testAgentListCLI_always_listDockerImagesWithAgent(mocker):
    """Test oxo agent list CLI command returns list of installed agents.

    This is just a smoke test to avoid a complex mock
    """
    image_list_mock = mocker.patch(
        "docker.models.images.ImageCollection.list", return_value=[]
    )

    runner = testing.CliRunner()

    result = runner.invoke(rootcli.rootcli, ["agent", "list"])

    assert "Agents listed successfully" in result.output
    image_list_mock.assert_called_once()
