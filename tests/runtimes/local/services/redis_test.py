"""Test local Redis service.

Tests marked with `docker` require access to working docker instance (socket or host). Make sure to disable them
on instances missing docker.
"""

import pytest
from pytest_mock import plugin

from ostorlab.runtimes.local import snapshot
from ostorlab.runtimes.local.services import container_exec
from ostorlab.runtimes.local.services import redis


@pytest.mark.docker
def testLocalRedis_onOperationalConditions_redisIsStarted() -> None:
    """Test service is healthy after start and unhealthy after stop."""
    lr = redis.LocalRedis(name="test_redis", network="test_network")
    lr.start()

    assert lr.is_healthy is True
    lr.stop()

    assert lr.is_healthy is False


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
