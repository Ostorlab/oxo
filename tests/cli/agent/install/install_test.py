"""Unit tests for the CLI agent install command."""

import logging
import re

import httpx
import tenacity
import docker.errors
from click import testing
from docker.models import images as images_model

from ostorlab.apis.runners import public_runner
from ostorlab.cli import rootcli
from ostorlab.cli import install_agent


def testAgentInstallCLI_whenRequiredOptionAgentKeyIsMissing_showMessage():
    """Test oxo agent install CLI command without the required agent_key option.
    Should show help message, and confirm the --agent option is missing.
    """
    runner = testing.CliRunner()

    result = runner.invoke(rootcli.rootcli, ["agent", "install"])

    assert "Usage: rootcli agent install [OPTIONS]" in result.output
    assert "Try 'rootcli agent install --help' for help." in result.output
    assert "Error: Missing argument" in result.output


def testAgentInstallCLI_whenAgentDoesNotExist_commandExitsWithError(httpx_mock, mocker):
    """Test oxo agent install CLI command with a wrong agent_key value.
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
    """Test oxo agent install CLI command with a valid agent_key value should install the agent."""

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


def testInstall_whenAgentImageIsPresent_logsAgentExistsMessage(mocker, caplog):
    """Ensure existing-agent install messages are available to persisted logging."""
    mocker.patch(
        "ostorlab.cli.agent_fetcher.get_details",
        return_value={
            "dockerLocation": "ostorlab.store/library/busybox",
            "key": "agent/ostorlab/dependency_confusion",
            "versions": {"versions": [{"version": "1.0.0"}]},
        },
    )
    mocker.patch("ostorlab.cli.install_agent._is_image_present", return_value=True)

    with caplog.at_level(logging.INFO, logger="ostorlab.cli.install_agent"):
        install_agent.install(
            agent_key="agent/ostorlab/dependency_confusion",
            docker_client=mocker.MagicMock(),
        )

    assert "agent/ostorlab/dependency_confusion already exist." in caplog.text


def testAgentInstallCLI_whenPullFails_retries(mocker, httpx_mock):
    """Test agent install retries on pull failure."""

    api_call_response = {
        "data": {
            "agent": {
                "name": "some_agent",
                "dockerLocation": "ostorlab.store/some_agent",
                "key": "agent/org/some_agent",
                "versions": {"versions": [{"version": "1.0.0"}]},
            }
        }
    }
    httpx_mock.add_response(
        url=public_runner.PUBLIC_GRAPHQL_ENDPOINT, json=api_call_response
    )

    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_docker_working", return_value=True
    )
    mocker.patch("ostorlab.cli.install_agent._is_image_present", return_value=False)

    # Mock docker to raise an error
    pull_mock = mocker.MagicMock(
        side_effect=docker.errors.APIError("some connection error")
    )
    mock_client = mocker.MagicMock()
    mock_client.api.pull = pull_mock
    mocker.patch("docker.from_env", return_value=mock_client)

    # Patch wait to be fast
    mocker.patch.object(install_agent._do_install.retry, "wait", tenacity.wait_fixed(0))

    runner = testing.CliRunner()
    result = runner.invoke(
        rootcli.rootcli, ["agent", "install", "agent/org/some_agent"]
    )

    # tenacity should have tried RETRY_ATTEMPTS times
    assert pull_mock.call_count == install_agent.RETRY_ATTEMPTS
    assert result.exit_code == 2


def testAgentInstallCLI_whenPullSucceedsAfterRetry_installsSuccessfully(
    mocker, httpx_mock
):
    """Test agent install succeeds if a retry eventually works."""

    api_call_response = {
        "data": {
            "agent": {
                "name": "some_agent",
                "dockerLocation": "ostorlab.store/some_agent",
                "key": "agent/org/some_agent",
                "versions": {"versions": [{"version": "1.0.0"}]},
            }
        }
    }
    httpx_mock.add_response(
        url=public_runner.PUBLIC_GRAPHQL_ENDPOINT, json=api_call_response
    )

    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_docker_working", return_value=True
    )
    mocker.patch("ostorlab.cli.install_agent._is_image_present", return_value=False)

    pull_mock = mocker.MagicMock()
    # First call raises error, second call returns successful log
    pull_mock.side_effect = [
        docker.errors.APIError("temporary error"),
        [{"status": "Download complete", "id": "123"}],
    ]
    mock_client = mocker.MagicMock()
    mock_client.api.pull = pull_mock
    mocker.patch("docker.from_env", return_value=mock_client)

    mock_image = mocker.MagicMock()
    mocker.patch("ostorlab.cli.install_agent._get_image", return_value=mock_image)

    mocker.patch.object(install_agent._do_install.retry, "wait", tenacity.wait_fixed(0))

    runner = testing.CliRunner()
    result = runner.invoke(
        rootcli.rootcli, ["agent", "install", "agent/org/some_agent"]
    )

    assert pull_mock.call_count == 2
    assert "Installation successful" in result.output
    assert result.exit_code == 0


def testInstallAgent_whenApiKeyProvided_passesTokenAsAuthConfigToPull(mocker):
    """When api_key is provided, the token is fetched and passed as auth_config to the pull."""
    agent_details = {
        "dockerLocation": "registry.ostorlab.co/agent_ot1_bigfuzzer",
        "key": "agent/ot1/bigFuzzer",
        "versions": {"versions": [{"version": "1.0.0"}]},
    }
    mocker.patch("ostorlab.cli.agent_fetcher.get_details", return_value=agent_details)
    mocker.patch("ostorlab.cli.install_agent._is_image_present", return_value=False)

    mock_client = mocker.MagicMock()
    mock_image = mocker.MagicMock()
    mocker.patch("ostorlab.cli.install_agent._get_image", return_value=mock_image)
    pull_logs_mock = mocker.patch(
        "ostorlab.cli.install_agent._pull_logs", return_value=[]
    )

    token_response = {
        "data": {"generateAgentImageDownloadToken": {"token": "test.jwt.token"}}
    }
    mock_runner = mocker.MagicMock()
    mock_runner.execute.return_value = token_response
    mocker.patch(
        "ostorlab.cli.install_agent.authenticated_runner.AuthenticatedAPIRunner",
        return_value=mock_runner,
    )

    install_agent.install(
        agent_key="agent/ot1/bigFuzzer",
        docker_client=mock_client,
        api_key="test_api_key",
    )

    mock_runner.execute.assert_called_once()
    mock_client.login.assert_not_called()
    pull_logs_mock.assert_called_once()
    assert pull_logs_mock.call_args.kwargs["auth_config"] == {
        "username": "token",
        "password": "test.jwt.token",
    }
    mock_image.tag.assert_called_once()


def testInstallAgent_whenApiKeyIsNone_skipsTokenFetchAndPullsAnonymously(mocker):
    """When api_key is None, no token is fetched and pull is called with auth_config=None."""
    agent_details = {
        "dockerLocation": "registry.ostorlab.co/agent_ot1_bigfuzzer",
        "key": "agent/ot1/bigFuzzer",
        "versions": {"versions": [{"version": "1.0.0"}]},
    }
    mocker.patch("ostorlab.cli.agent_fetcher.get_details", return_value=agent_details)
    mocker.patch("ostorlab.cli.install_agent._is_image_present", return_value=False)

    mock_client = mocker.MagicMock()
    mock_image = mocker.MagicMock()
    mocker.patch("ostorlab.cli.install_agent._get_image", return_value=mock_image)
    pull_logs_mock = mocker.patch(
        "ostorlab.cli.install_agent._pull_logs", return_value=[]
    )

    mock_runner = mocker.MagicMock()
    mocker.patch(
        "ostorlab.cli.install_agent.authenticated_runner.AuthenticatedAPIRunner",
        return_value=mock_runner,
    )

    install_agent.install(
        agent_key="agent/ot1/bigFuzzer",
        docker_client=mock_client,
        api_key=None,
    )

    mock_runner.execute.assert_not_called()
    mock_client.login.assert_not_called()
    pull_logs_mock.assert_called_once()
    assert pull_logs_mock.call_args.kwargs["auth_config"] is None
    mock_image.tag.assert_called_once()


def testPullLogs_whenAuthConfigProvided_forwardsItToDockerApiPull(mocker):
    """_pull_logs forwards the auth_config dict to docker_client.api.pull."""
    mock_client = mocker.MagicMock()
    mock_client.api.pull.return_value = iter([])

    list(
        install_agent._pull_logs(
            mock_client,
            "registry.ostorlab.co/agent_ot1_bigfuzzer",
            tag="v1.0.0",
            auth_config={"username": "token", "password": "test.jwt.token"},
        )
    )

    mock_client.api.pull.assert_called_once_with(
        "registry.ostorlab.co/agent_ot1_bigfuzzer",
        tag="v1.0.0",
        stream=True,
        decode=True,
        auth_config={"username": "token", "password": "test.jwt.token"},
    )
