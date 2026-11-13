"""Test local Redis service.

Tests marked with `docker` require access to working docker instance (socket or host). Make sure to disable them
on instances missing docker.
"""

from __future__ import annotations

import collections.abc
import time
import uuid

import docker
import pytest
import tenacity
from pytest_mock import plugin

from ostorlab.runtimes import docker_cleanup
from ostorlab.runtimes.local import snapshot
from ostorlab.runtimes.local.services import container_exec
from ostorlab.runtimes.local.services import redis


@pytest.mark.docker
def testLocalRedis_onOperationalConditions_redisIsStarted(
    durable_redis: tuple[docker.DockerClient, redis.LocalRedis, str],
) -> None:
    """Test service is healthy after start and unhealthy after stop."""
    _, local_redis, _ = durable_redis

    assert local_redis.is_healthy is True
    local_redis.stop()

    assert local_redis.is_healthy is False


def testLocalRedisRestore_always_pipesRestoreCommandsInsideRedisContainer(
    mocker: plugin.MockerFixture,
) -> None:
    """Keys are restored with `RESTORE ... REPLACE` commands sent by `redis-cli --pipe` once Redis answers."""
    mocker.patch("docker.from_env")
    lr = redis.LocalRedis(name="test_redis", network="test_network")
    run = mocker.patch.object(
        container_exec, "run", side_effect=[b"PONG\n", b"errors: 0"]
    )

    lr.restore(
        [
            snapshot.RedisKey(key=b"dedup", ttl_ms=0, value=b"\x00v"),
            snapshot.RedisKey(key=b"lock", ttl_ms=1500, value=b"w"),
        ]
    )

    assert run.call_args_list[0].args[2] == redis.REDIS_READINESS_COMMAND
    restore_call = run.call_args_list[1]
    assert restore_call.args[2][:2] == ["sh", "-c"]
    assert "redis-cli --pipe" in restore_call.args[2][2]
    assert restore_call.kwargs["files"] == {
        redis.REDIS_RESTORE_FILE: (
            b"*5\r\n$7\r\nRESTORE\r\n$5\r\ndedup\r\n$1\r\n0\r\n$2\r\n\x00v\r\n$7\r\nREPLACE\r\n"
            b"*5\r\n$7\r\nRESTORE\r\n$4\r\nlock\r\n$4\r\n1500\r\n$1\r\nw\r\n$7\r\nREPLACE\r\n"
        )
    }


def testLocalRedisRestore_whenRedisIsNotReadyYet_waitsForIt(
    mocker: plugin.MockerFixture,
) -> None:
    """A running Redis container may not accept connections yet."""
    mocker.patch("docker.from_env")
    lr = redis.LocalRedis(name="test_redis", network="test_network")
    run = mocker.patch.object(
        container_exec,
        "run",
        side_effect=[b"Could not connect", b"PONG", b"errors: 0"],
    )

    lr.restore([snapshot.RedisKey(key=b"k", ttl_ms=0, value=b"v")])

    assert run.call_count == 3


def testLocalRedisRestore_whenNoKeys_doesNothing(
    mocker: plugin.MockerFixture,
) -> None:
    """A universe without Redis state has nothing to restore."""
    mocker.patch("docker.from_env")
    lr = redis.LocalRedis(name="test_redis", network="test_network")
    run = mocker.patch.object(container_exec, "run")

    lr.restore([])

    run.assert_not_called()


@tenacity.retry(
    stop=tenacity.stop_after_attempt(150),
    wait=tenacity.wait_fixed(0.2),
    retry=tenacity.retry_if_exception_type(container_exec.ExecError),
    reraise=True,
)
def _run_redis(
    client: docker.DockerClient, local_redis: redis.LocalRedis, command: list[str]
) -> bytes:
    return container_exec.run(client, local_redis.service, command)


@tenacity.retry(
    stop=tenacity.stop_after_attempt(150),
    wait=tenacity.wait_fixed(0.2),
    retry=tenacity.retry_if_result(lambda cleaned: cleaned is False),
)
def _cleanup_redis(client: docker.DockerClient, scan_name: str) -> bool:
    return docker_cleanup.cleanup_scan_docker_resources(client, scan_name)


@pytest.fixture
def durable_redis() -> collections.abc.Iterator[
    tuple[docker.DockerClient, redis.LocalRedis, str]
]:
    """Create a Redis universe with names owned only by this test."""
    scan_name = f"redis_durability_{uuid.uuid4().hex}"
    client = docker.from_env()
    local_redis = redis.LocalRedis(name=scan_name, network=f"network_{scan_name}")
    try:
        local_redis.start()
        assert _run_redis(client, local_redis, ["redis-cli", "ping"]) == b"PONG\n"
        status = _run_redis(client, local_redis, ["cat", "/proc/1/status"])
        effective_uid = next(
            line for line in status.splitlines() if line.startswith(b"Uid:")
        ).split()[2]
        redis_uid = _run_redis(client, local_redis, ["id", "-u", "redis"]).strip()
        assert effective_uid == redis_uid
        assert effective_uid != b"0"
        yield client, local_redis, scan_name
    finally:
        _cleanup_redis(client, scan_name)
        client.close()


@pytest.mark.docker
@pytest.mark.parametrize("replacement_kind", ["service", "container"])
def testLocalRedis_whenServiceOrContainerReplaced_preservesBinaryAssetAndSet(
    durable_redis: tuple[docker.DockerClient, redis.LocalRedis, str],
    replacement_kind: str,
) -> None:
    """A replacement service recovers binary assets and agent set state."""
    client, local_redis, scan_name = durable_redis
    ipa = b"PK\x03\x04" + bytes(range(256)) * 4096
    assert (
        container_exec.run(
            client,
            local_redis.service,
            ["sh", "-c", "redis-cli -x SET ios:ipa < /tmp/asset.ipa"],
            files={"asset.ipa": ipa},
        )
        == b"OK\n"
    )
    _run_redis(
        client, local_redis, ["redis-cli", "SADD", "agent:processed", "first", "second"]
    )
    time.sleep(2)
    assert local_redis.service is not None
    previous_containers = client.containers.list(
        filters={"label": f"com.docker.swarm.service.name=redis_{scan_name}"}
    )
    assert len(previous_containers) == 1
    if replacement_kind == "service":
        previous_service_id = local_redis.service.id
        local_redis.stop()
        try:
            previous_containers[0].wait(timeout=30)
        except docker.errors.NotFound:
            pass
        replacement = redis.LocalRedis(name=scan_name, network=f"network_{scan_name}")
        replacement.start()
        assert replacement.service is not None
        assert replacement.service.id != previous_service_id
    else:
        previous_containers[0].kill(signal="SIGKILL")
        replacement = local_redis

    assert (
        _run_redis(client, replacement, ["redis-cli", "--raw", "GET", "ios:ipa"])
        == ipa + b"\n"
    )
    assert set(
        _run_redis(
            client, replacement, ["redis-cli", "--raw", "SMEMBERS", "agent:processed"]
        ).splitlines()
    ) == {b"first", b"second"}
    assert (
        _run_redis(
            client, replacement, ["redis-cli", "--raw", "CONFIG", "GET", "appendonly"]
        )
        == b"appendonly\nyes\n"
    )
    assert (
        _run_redis(
            client, replacement, ["redis-cli", "--raw", "CONFIG", "GET", "appendfsync"]
        )
        == b"appendfsync\neverysec\n"
    )
    current_containers = client.containers.list(
        filters={"label": f"com.docker.swarm.service.name=redis_{scan_name}"}
    )
    assert len(current_containers) == 1
    assert current_containers[0].id != previous_containers[0].id
