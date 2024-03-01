"""Unit tests for the CLI agent install command."""

import re

import httpx
from click import testing
from docker.models import images as images_model

from ostorlab.apis.runners import public_runner
from ostorlab.cli import rootcli


def testAgentInstallCLI_whenRequiredOptionAgentKeyIsMissing_showMessage():
    """Test ostorlab agent install CLI command without the required agent_key option.
    Should show help message, and confirm the --agent option is missing.
    """
    runner = testing.CliRunner()

    result = runner.invoke(rootcli.rootcli, ["agent", "install"])

    assert "Usage: rootcli agent install [OPTIONS]" in result.output
    assert "Try 'rootcli agent install --help' for help." in result.output
    assert "Error: Missing argument" in result.output


def testAgentInstallCLI_whenAgentDoesNotExist_commandExitsWithError(httpx_mock, mocker):
    """Test ostorlab agent install CLI command with a wrong agent_key value.
    Should show message.
    """

    api_call_response = {
        "errors": [
            {
                "message": "Agent with key : agent/os/not_found does not exist.",
                "locations": [{"line": 2, "column": 3}],
                "path": ["agent"],
            }
        ]
    }

    def _custom_matcher(request):
        matcher = re.compile(r"http\+docker://(.*)/version")
        if re.match(matcher, str(request.url)) is not None:
            return httpx.Response(200, json={"ApiVersion": "1.42"})
        if str(request.url) == public_runner.PUBLIC_GRAPHQL_ENDPOINT:
            return httpx.Response(200, json=api_call_response)

    httpx_mock.add_callback(_custom_matcher)

    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_docker_working", return_value=True
    )
    runner = testing.CliRunner()
    result = runner.invoke(rootcli.rootcli, ["agent", "install", "agent/wrong/key"])

    assert "ERROR:" in result.output, result.output
    assert result.exit_code == 2


def testAgentInstallCLI_whenAgentExists_installsAgent(mocker, httpx_mock):
    """Test ostorlab agent install CLI command with a valid agent_key value should install the agent."""

    image_pull_mock = mocker.patch("docker.api.client.APIClient.pull", autospec=True)
    image_get_mock = mocker.patch(
        "docker.models.images.ImageCollection.get", return_value=images_model.Image()
    )
    tag_image_mock = mocker.patch("docker.models.images.Image.tag", return_value=True)
    mocker.patch("ostorlab.cli.install_agent._is_image_present", return_value=False)

    api_call_response = {
        "data": {
            "agent": {
                "name": "bigFuzzer",
                "gitLocation": "",
                "yamlFileLocation": "",
                "dockerLocation": "ostorlab.store/library/busybox",
                "key": "agent/OS/some_agentd",
                "versions": {"versions": [{"version": "1.0.0"}]},
            }
        }
    }

    def _custom_matcher(request):
        matcher_version = re.compile(r"http\+docker://(.*)/version")
        matcher_json = re.compile(r"http\+docker://(.*)/json")
        if re.match(matcher_version, str(request.url)) is not None:
            return httpx.Response(200, json={"ApiVersion": "1.42"})
        if re.match(matcher_json, str(request.url)) is not None:
            return httpx.Response(200, json={})
        if str(request.url) == public_runner.PUBLIC_GRAPHQL_ENDPOINT:
            return httpx.Response(200, json=api_call_response)

    httpx_mock.add_callback(_custom_matcher)

    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_docker_working", return_value=True
    )
    runner = testing.CliRunner()
    result = runner.invoke(rootcli.rootcli, ["agent", "install", "agent/OT1/bigFuzzer"])
    image_pull_mock.assert_called()
    image_get_mock.assert_called()
    tag_image_mock.assert_called()
    assert "Installation successful" in result.output
