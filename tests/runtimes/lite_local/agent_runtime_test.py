"""Tests for lite runtime agent configuration mounts."""

import pathlib

import docker
import pytest
from pytest_mock import plugin

from ostorlab.runtimes import definitions
from ostorlab.runtimes.lite_local import agent_runtime


def testReplaceVariableMounts_whenConfigurationOverridden_usesSelectedDirectory(
    mocker: plugin.MockerFixture,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
) -> None:
    """Agent configuration mounts follow the selected private directory."""
    private_dir = tmp_path / "private"
    monkeypatch.setenv("OSTORLAB_PRIVATE_DIR", str(private_dir))
    mocker.patch(
        "ostorlab.runtimes.definitions.AgentSettings.container_image",
        new_callable=mocker.PropertyMock,
        return_value="agent_org_name:v1.0.0",
    )
    docker_client = mocker.MagicMock(spec=docker.DockerClient)
    runtime_agent = agent_runtime.AgentRuntime(
        definitions.AgentSettings(key="agent/org/name"),
        "42",
        docker_client,
        bus_url="amqp://localhost",
        bus_vhost="/",
        bus_management_url="http://localhost",
        bus_exchange_topic="test",
        redis_url="redis://localhost",
        tracing_collector_url="http://localhost",
    )

    assert runtime_agent.replace_variable_mounts(["$CONFIG_HOME:/config"]) == [
        f"{private_dir.resolve()}:/config"
    ]
