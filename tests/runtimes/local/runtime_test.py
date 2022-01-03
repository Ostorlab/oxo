"""Unittest for local runtime."""
import docker
import pytest

from ostorlab.assets import android_apk
from ostorlab.runtimes import definitions
from ostorlab.runtimes.local import runtime as local_runtime


@pytest.mark.skip(reason='Missing inject asset agent.')
@pytest.mark.docker
def testRuntimeScan_whenEmptyRunDefinition_runtimeServicesAreRunning():
    local_runtime_instance = local_runtime.LocalRuntime()
    asset = android_apk.AndroidApk(content=b'APK')
    agent_run_definition = definitions.AgentGroupDefinition(agents=[])

    local_runtime_instance.scan(agent_group_definition=agent_run_definition, asset=asset)

    docker_client = docker.from_env()

    services = docker_client.services.list(filters={'label': f'ostorlab.universe={local_runtime_instance.name}'})
    assert any(s.name.startswith('mq_') for s in services)


@pytest.mark.skip(reason='Missing sample agents to test with.')
@pytest.mark.docker
def testRuntimeScan_whenValidAgentRunDefinitionAndAssetAreProvided_scanIsRunning():
    local_runtime_instance = local_runtime.LocalRuntime()
    asset = android_apk.AndroidApk(content=b'APK')
    agent_run_definition = definitions.AgentGroupDefinition(agents=[])

    local_runtime_instance.scan(agent_group_definition=agent_run_definition, asset=asset)

    docker_client = docker.from_env()

    services = docker_client.services.list(filters={'label': f'ostorlab.universe={local_runtime_instance.name}'})
    assert any(s.name.startswith('mq_') for s in services)
    assert any(s.name.starts_with('agent_') for s in services)
    # TODO(alaeddine): check for asset injection.

