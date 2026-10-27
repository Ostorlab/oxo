"""Memory admission and service resource configuration tests."""

from __future__ import annotations

import typing
import uuid
from unittest import mock

import docker
import pytest
from docker.models import services
from pytest_mock import plugin

from ostorlab.runtimes import definitions
from ostorlab.runtimes.local import agent_runtime
from ostorlab.runtimes.local import resources
from ostorlab.runtimes.local import runtime as local_runtime
from ostorlab.runtimes.local.models import models
from ostorlab.runtimes.local.services import jaeger
from ostorlab.runtimes.local.services import mq
from ostorlab.runtimes.local.services import redis


@pytest.fixture
def docker_client(mocker: plugin.MockerFixture) -> mock.MagicMock:
    """Fake Docker at the API boundary while preserving runtime configuration logic."""
    client = mock.MagicMock()
    mocker.patch.object(docker, "from_env", return_value=client)
    client.configs.get.side_effect = docker.errors.NotFound("missing")
    client.configs.create.return_value.id = "config-id"
    client.images.get.return_value.labels = {
        "agent_definition": "name: worker\nkind: Agent\nin_selectors: []\nout_selectors: []\n"
    }
    client.images.list.return_value = [mocker.Mock(tags=["agent_org_worker:v1.0.0"])]
    return client


@pytest.mark.parametrize(
    ("service_type", "environment", "default_limit"),
    [
        (mq.LocalRabbitMQ, "OSTORLAB_MQ_MEMORY_LIMIT_BYTES", 2 * 1024**3),
        (redis.LocalRedis, "OSTORLAB_REDIS_MEMORY_LIMIT_BYTES", 512 * 1024**2),
        (jaeger.LocalJaeger, "OSTORLAB_JAEGER_MEMORY_LIMIT_BYTES", 512 * 1024**2),
    ],
)
@pytest.mark.parametrize("override", [None, "536870913"])
def testServiceStart_withMemoryBudget_reservesHeadroomAndCapsMemory(
    docker_client: mock.MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    service_type: type[mq.LocalRabbitMQ | redis.LocalRedis | jaeger.LocalJaeger],
    environment: str,
    default_limit: int,
    override: str | None,
) -> None:
    monkeypatch.delenv(environment, raising=False)
    if override is not None:
        monkeypatch.setenv(environment, override)
    service_type(name="42", network="network").start()
    limit = default_limit if override is None else int(override)
    spec = docker_client.services.create.call_args.kwargs
    assert spec["resources"] == {
        "Limits": {"MemoryBytes": limit},
        "Reservations": {"MemoryBytes": (limit * 5 + 3) // 4},
        "MemorySwappiness": None,
    }
    if service_type is mq.LocalRabbitMQ:
        config = docker_client.configs.create.call_args.kwargs["data"]
        assert (
            f"{{vm_memory_high_watermark, {{absolute, {limit // 2}}}}}".encode()
            in config
        )
        assert spec["hostname"] == "mq"
        assert spec["mounts"] == [
            {
                "Target": "/var/lib/rabbitmq",
                "Source": "42_mq_data",
                "Type": "volume",
                "ReadOnly": False,
            }
        ]


@pytest.mark.parametrize(
    ("group_limit", "image_limit", "environment_limit", "expected"),
    [
        (None, None, None, 4 * 1024**3),
        (None, None, "700001", 700001),
        (None, 800001, "700001", 800001),
        (900001, 800001, "700001", 900001),
    ],
)
def testAgentStart_withMemoryOverrides_usesMostSpecificBudget(
    docker_client: mock.MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    group_limit: int | None,
    image_limit: int | None,
    environment_limit: str | None,
    expected: int,
) -> None:
    monkeypatch.delenv("OSTORLAB_AGENT_MEMORY_LIMIT_BYTES", raising=False)
    if environment_limit is not None:
        monkeypatch.setenv("OSTORLAB_AGENT_MEMORY_LIMIT_BYTES", environment_limit)
    if image_limit is not None:
        docker_client.images.get.return_value.labels["agent_definition"] += (
            f"mem_limit: {image_limit}\n"
        )
    agent = agent_runtime.AgentRuntime(
        definitions.AgentSettings(key="agent/org/worker", mem_limit=group_limit),
        "42",
        docker_client,
        mq.LocalRabbitMQ("42", "network"),
        redis.LocalRedis("42", "network"),
        None,
    )
    agent.create_agent_service("network", replicas=0)
    spec = docker_client.services.create.call_args.kwargs
    assert spec["resources"]["Limits"]["MemoryBytes"] == expected
    assert spec["resources"]["Reservations"]["MemoryBytes"] == (expected * 5 + 3) // 4
    assert spec["resources"]["MemorySwappiness"] is None
    assert spec["mode"]["replicated"]["Replicas"] == 0


@pytest.mark.parametrize("invalid", ["0", "-1", "true", "12.5", ""])
def testServiceStart_withInvalidMemoryBudget_rejectsConfiguration(
    docker_client: mock.MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    invalid: str,
) -> None:
    monkeypatch.setenv("OSTORLAB_REDIS_MEMORY_LIMIT_BYTES", invalid)
    with pytest.raises(ValueError, match="positive integer"):
        redis.LocalRedis("42", "network").start()
    docker_client.services.create.assert_not_called()


@pytest.mark.parametrize("invalid", [0, -1, True])
def testAgentStart_withInvalidGroupBudget_rejectsConfiguration(
    docker_client: mock.MagicMock,
    invalid: int,
) -> None:
    agent = agent_runtime.AgentRuntime(
        definitions.AgentSettings(key="agent/org/worker", mem_limit=invalid),
        "42",
        docker_client,
        mq.LocalRabbitMQ("42", "network"),
        redis.LocalRedis("42", "network"),
        None,
    )
    with pytest.raises(ValueError, match="positive integer"):
        agent.create_agent_service("network")
    docker_client.services.create.assert_not_called()


@pytest.mark.parametrize(("replicas", "expected"), [(0, 0), (None, 1), (-1, 1), (3, 3)])
def testAgentGroupFromApi_withReplicaCount_preservesDeliberateZero(
    replicas: int | None,
    expected: int,
) -> None:
    group = definitions.AgentGroupDefinition.from_api_response(
        {
            "key": "agentgroup/org/group",
            "agents": [{"key": "agent/org/worker", "replicas": replicas}],
        }
    )
    assert group.agents[0].replicas == expected


@pytest.mark.parametrize("worker_pending", [False, True])
def testLocalScan_withWorkerReplicaStates_enforcesStartupHealth(
    docker_client: mock.MagicMock,
    mocker: plugin.MockerFixture,
    db_engine_path: str,
    worker_pending: bool,
) -> None:
    """Keep zero replicas stopped and reject positive replicas that remain pending."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    mocker.patch("time.sleep")
    created: list[mock.MagicMock] = []

    def create_service(**kwargs: typing.Any) -> mock.MagicMock:
        service = mock.MagicMock()
        service.name = kwargs["name"]
        service.attrs = {
            "Spec": {
                "Labels": kwargs["labels"],
                "Mode": {"Replicated": kwargs["mode"]["replicated"]},
                "TaskTemplate": {"RestartPolicy": kwargs["restart_policy"]},
            }
        }
        desired = kwargs["mode"]["replicated"]["Replicas"]
        service.tasks.return_value = [
            {
                "Status": {
                    "State": "running",
                    "ContainerStatus": {"ContainerID": "container"},
                }
            }
            for _ in range(desired)
        ]
        if worker_pending is True and service.name.startswith("agent_"):
            service.tasks.return_value = [
                {"Status": {"State": "pending", "Err": "insufficient resources"}}
            ]
        created.append(service)
        return service

    docker_client.services.create.side_effect = create_service
    docker_client.services.list.side_effect = lambda **kwargs: created
    docker_client.containers.get.return_value.exec_run.return_value = mocker.Mock(
        exit_code=0, output=b"ready"
    )
    group = definitions.AgentGroupDefinition(
        agents=[
            definitions.AgentSettings(
                key="agent/org/worker", replicas=1 if worker_pending is True else 0
            )
        ]
    )
    runtime = local_runtime.LocalRuntime(scan_id="42", run_default_agents=False)
    assert runtime.can_run(group) is True
    if worker_pending is True:
        with pytest.raises(
            local_runtime.AgentNotHealthy, match="insufficient resources"
        ):
            runtime.scan(
                title="Pending worker", agent_group_definition=group, assets=None
            )
        return
    scan = runtime.scan(
        title="Zero replicas", agent_group_definition=group, assets=None
    )

    assert scan is not None
    worker = next(service for service in created if service.name.startswith("agent_"))
    assert worker.attrs["Spec"]["Mode"]["Replicated"]["Replicas"] == 0
    worker.remove.assert_not_called()


@pytest.mark.docker
def testSwarmResources_withZeroReplicaService_acceptsHeadroomReservation() -> None:
    """Swarm accepts a reservation above the cap; this creates no containers."""
    client = docker.from_env()
    service = None
    try:
        service = typing.cast(
            typing.Callable[..., services.Service], client.services.create
        )(
            image="alpine:3.21",
            name=f"oxo-resource-check-{uuid.uuid4().hex}",
            mode=docker.types.ServiceMode("replicated", replicas=0),
            resources=resources.swarm_resources(128 * 1024**2),
        )
        service.reload()
        spec = service.attrs["Spec"]
        assert spec["Mode"]["Replicated"]["Replicas"] == 0
        assert (
            spec["TaskTemplate"]["Resources"]["Limits"]["MemoryBytes"] == 128 * 1024**2
        )
        assert (
            spec["TaskTemplate"]["Resources"]["Reservations"]["MemoryBytes"]
            == 160 * 1024**2
        )
    finally:
        if service is not None:
            typing.cast(typing.Callable[[], None], service.remove)()
        client.close()


@pytest.mark.parametrize(
    "service_type", [mq.LocalRabbitMQ, redis.LocalRedis, jaeger.LocalJaeger]
)
def testServiceHealth_withPendingTasks_returnsFalseAfterRetries(
    docker_client: mock.MagicMock,
    mocker: plugin.MockerFixture,
    service_type: type[mq.LocalRabbitMQ | redis.LocalRedis | jaeger.LocalJaeger],
) -> None:
    """An exhausted health check must never return a truthy Future(False)."""
    mocker.patch("time.sleep")
    docker_client.services.create.return_value.tasks.return_value = [
        {
            "Status": {
                "State": "pending",
                "Err": "no suitable node (insufficient resources)",
            }
        }
    ]
    service = service_type(name="42", network="network")
    service.start()
    assert service.is_service_healthy() is False
