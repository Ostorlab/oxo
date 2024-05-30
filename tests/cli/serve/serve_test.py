"""Unit tests for the serve command."""

from click.testing import CliRunner
from pytest_mock import plugin

from ostorlab.cli import rootcli


def testOstorlabServe_whenRefreshApiKeyFlagIsProvided_refreshApiKey(
    mocker: plugin.MockerFixture,
) -> None:
    """Test the serve command with the refresh-api-key flag. Should refresh the API key."""
    mocked_refresh_api_key = mocker.patch(
        "ostorlab.runtimes.local.models.models.APIKey.refresh"
    )
    mocker.patch("ostorlab.serve_app.app.create_app")

    runner = CliRunner()
    result = runner.invoke(rootcli.rootcli, ["serve", "--refresh-api-key"])

    assert mocked_refresh_api_key.called is True
    assert "API key refreshed" in result.output


def testOstorlabServe_whenRefreshApiKeyFlagIsNotProvided_getOrCreateApiKey(
    mocker: plugin.MockerFixture,
) -> None:
    """Test the serve command without the refresh-api-key flag. Should get or create the API key."""
    mocked_refresh_api_key = mocker.patch(
        "ostorlab.runtimes.local.models.models.APIKey.refresh"
    )
    mocker.patch("ostorlab.serve_app.app.create_app")

    runner = CliRunner()
    result = runner.invoke(rootcli.rootcli, ["serve"])

    assert mocked_refresh_api_key.called is False
    assert "API key refreshed" not in result.output
