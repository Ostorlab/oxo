"""Tests for AgentPersistMixin module."""

import ipaddress

import pytest
import redis
from pytest_mock import plugin

from ostorlab.agent.mixins import agent_persist_mixin
from ostorlab.runtimes import definitions as runtime_definitions
from ostorlab.runtimes.local.services import redis as local_redis_service


@pytest.mark.parametrize("clean_redis_data", ["redis://localhost:6379"], indirect=True)
@pytest.mark.asyncio
@pytest.mark.docker
async def testAgentPersistMixin_whenSetIsAdded_setIsPersisted(
    redis_service: local_redis_service.LocalRedis, clean_redis_data: None
) -> None:
    """Test proper storage and access of set API."""
    del redis_service, clean_redis_data
    settings = runtime_definitions.AgentSettings(
        key="agent/ostorlab/debug", redis_url="redis://localhost:6379"
    )
    mixin = agent_persist_mixin.AgentPersistMixin(settings)

    assert mixin.set_is_member("test", "A") is False
    mixin.set_add("test", b"A")
    mixin.set_add("test", "B")
    assert mixin.set_is_member("test", "A") is True
    assert mixin.set_is_member("test", "B") is True
    assert mixin.set_is_member("test", "C") is False
    assert mixin.set_len("test") == 2
    assert mixin.set_members("test") == {b"A", b"B"}
    mixin.add("myKey", b"myVal")
    assert mixin.get("myKey") == b"myVal"
    assert mixin.get("myKey1") is None
    assert mixin.value_type("test") == "set"
    assert mixin.value_type("myKey") == "string"
    assert mixin.value_type("myKey1") == "none"


@pytest.mark.parametrize("clean_redis_data", ["redis://localhost:6379"], indirect=True)
@pytest.mark.asyncio
@pytest.mark.docker
async def testAgentPersistMixinExists_whenKeyExists_returnTrue(
    redis_service: local_redis_service.LocalRedis,
    clean_redis_data: None,
) -> None:
    """Test AgentPersistMixin exists method."""
    settings = runtime_definitions.AgentSettings(
        key="agent/ostorlab/debug", redis_url="redis://localhost:6379"
    )
    mixin = agent_persist_mixin.AgentPersistMixin(settings)

    key = "thekey"
    assert mixin.exists(key) is False
    mixin.add(key, b"the_value")
    assert mixin.exists(key) is True


@pytest.mark.parametrize("clean_redis_data", ["redis://localhost:6379"], indirect=True)
@pytest.mark.asyncio
@pytest.mark.docker
async def testAgentPersistMixinDeleteKey_whenKeyExists_keyIsDeleted(
    mocker: plugin.MockerFixture,
    redis_service: local_redis_service.LocalRedis,
    clean_redis_data: None,
) -> None:
    """Test proper storage and access of set API."""
    del mocker, redis_service, clean_redis_data
    settings = runtime_definitions.AgentSettings(
        key="agent/ostorlab/debug", redis_url="redis://localhost:6379"
    )
    mixin = agent_persist_mixin.AgentPersistMixin(settings)

    mixin.set_add("test1", b"A")
    mixin.delete("test1")
    assert mixin.set_members("test") == set()


@pytest.mark.parametrize("clean_redis_data", ["redis://localhost:6379"], indirect=True)
@pytest.mark.asyncio
@pytest.mark.docker
async def testAgentPersistMixin_whenHashIsAdded_hashIsPersisted(
    mocker: plugin.MockerFixture,
    redis_service: local_redis_service.LocalRedis,
    clean_redis_data: None,
) -> None:
    """Test proper storage and access of Hash API."""
    del mocker, redis_service, clean_redis_data
    settings = runtime_definitions.AgentSettings(
        key="agent/ostorlab/debug", redis_url="redis://localhost:6379"
    )
    mixin = agent_persist_mixin.AgentPersistMixin(settings)

    assert mixin.hash_exists("hash_name", "key1") is False
    mixin.hash_add("hash_name", {"key1": "val1", "key2": "val2"})
    assert mixin.hash_exists("hash_name", "key1") is True
    assert mixin.hash_get("hash_name", "key2") == b"val2"
    assert mixin.hash_get("hash_name", "NoneExistingKey") is None
    assert b"key1" in mixin.hash_get_all("hash_name")
    assert b"key2" in mixin.hash_get_all("hash_name")


@pytest.mark.parametrize("clean_redis_data", ["redis://localhost:6379"], indirect=True)
@pytest.mark.asyncio
@pytest.mark.docker
async def testAgentPersistMixinCheckIpRangeExist_whenIpRangeIsCovered_returnTrue(
    mocker: plugin.MockerFixture,
    redis_service: local_redis_service.LocalRedis,
    clean_redis_data: None,
) -> None:
    """Test mixin.add_ip_network returns True if ip_range is added and False if the ip_range
    or one of his supersets already exits"""
    del mocker, redis_service, clean_redis_data
    settings = runtime_definitions.AgentSettings(
        key="agent/ostorlab/debug", redis_url="redis://localhost:6379"
    )
    mixin = agent_persist_mixin.AgentPersistMixin(settings)

    assert mixin.add_ip_network("test_ip", ipaddress.ip_network("8.8.8.0/23")) is True
    assert mixin.add_ip_network("test_ip", ipaddress.ip_network("8.8.8.0/24")) is False
    assert mixin.add_ip_network("test_ip", ipaddress.ip_network("8.8.8.0/23")) is False
    assert mixin.add_ip_network("test_ip", ipaddress.ip_network("8.8.8.0/24")) is False
    assert mixin.add_ip_network("test_ip", ipaddress.ip_network("8.8.8.0/31")) is False
    assert mixin.add_ip_network("test_ip", ipaddress.ip_network("8.8.8.0/22")) is True
    assert (
        mixin.add_ip_network("test_ip", ipaddress.ip_network("10.10.10.0/23")) is True
    )
    assert (
        mixin.add_ip_network("test_ip", ipaddress.ip_network("10.10.10.0/28")) is False
    )


@pytest.mark.parametrize("clean_redis_data", ["redis://localhost:6379"], indirect=True)
@pytest.mark.asyncio
@pytest.mark.docker
async def testAgentPersistMixinCheckIpRangeExist_withCallableKey_returnTrue(
    mocker: plugin.MockerFixture,
    redis_service: local_redis_service.LocalRedis,
    clean_redis_data: None,
) -> None:
    """Test mixin.add_ip_network returns True if ip_range is added and False if the ip_range
    or one of his supersets already exits"""
    del mocker, redis_service, clean_redis_data
    settings = runtime_definitions.AgentSettings(
        key="agent/ostorlab/debug", redis_url="redis://localhost:6379"
    )
    mixin = agent_persist_mixin.AgentPersistMixin(settings)

    assert (
        mixin.add_ip_network(
            "test_ip", ipaddress.ip_network("8.8.8.0/23"), lambda net: f"X_{net}_Y"
        )
        is True
    )
    assert (
        mixin.add_ip_network(
            "test_ip", ipaddress.ip_network("8.8.8.0/24"), lambda net: f"X_{net}_Y"
        )
        is False
    )
    assert (
        mixin.add_ip_network(
            "test_ip", ipaddress.ip_network("8.8.8.0/23"), lambda net: f"X_{net}_Y"
        )
        is False
    )
    assert (
        mixin.add_ip_network(
            "test_ip", ipaddress.ip_network("8.8.8.0/24"), lambda net: f"X_{net}_Y"
        )
        is False
    )
    assert (
        mixin.add_ip_network(
            "test_ip", ipaddress.ip_network("8.8.8.0/31"), lambda net: f"X_{net}_Y"
        )
        is False
    )
    assert (
        mixin.add_ip_network(
            "test_ip", ipaddress.ip_network("8.8.8.0/22"), lambda net: f"X_{net}_Y"
        )
        is True
    )
    assert (
        mixin.add_ip_network(
            "test_ip", ipaddress.ip_network("10.10.10.0/23"), lambda net: f"X_{net}_Y"
        )
        is True
    )
    assert (
        mixin.add_ip_network(
            "test_ip", ipaddress.ip_network("10.10.10.0/28"), lambda net: f"X_{net}_Y"
        )
        is False
    )


@pytest.mark.parametrize("clean_redis_data", ["redis://localhost:6379"], indirect=True)
@pytest.mark.asyncio
@pytest.mark.docker
async def testAgentPersistMixinCheckIpNetworkExist_whenIpRangeIsCovered_returnTrue(
    mocker: plugin.MockerFixture,
    redis_service: local_redis_service.LocalRedis,
    clean_redis_data: None,
) -> None:
    """Test mixin.ip_network_exist returns True if ip_range is added and False if the ip_range
    or one of his supersets already exits"""
    del mocker, redis_service, clean_redis_data
    settings = runtime_definitions.AgentSettings(
        key="agent/ostorlab/debug", redis_url="redis://localhost:6379"
    )
    mixin = agent_persist_mixin.AgentPersistMixin(settings)

    assert (
        mixin.ip_network_exists(
            "test_ip", ipaddress.ip_network("8.8.8.0/23"), lambda net: f"X_{net}_Y"
        )
        is False
    )
    mixin.add_ip_network(
        "test_ip", ipaddress.ip_network("8.8.8.0/23"), lambda net: f"X_{net}_Y"
    )
    assert (
        mixin.ip_network_exists(
            "test_ip", ipaddress.ip_network("8.8.8.0/23"), lambda net: f"X_{net}_Y"
        )
        is True
    )


@pytest.mark.parametrize("clean_redis_data", ["redis://localhost:6379"], indirect=True)
@pytest.mark.asyncio
@pytest.mark.docker
async def testAgentPersistMixinMarkSeen_whenKeyIsNew_returnTrueAndSetTtl(
    redis_service: local_redis_service.LocalRedis,
    clean_redis_data: None,
) -> None:
    """Test mark_seen marks a new key and sets its expiry."""
    del redis_service, clean_redis_data
    settings = runtime_definitions.AgentSettings(
        key="agent/ostorlab/debug", redis_url="redis://localhost:6379"
    )
    mixin = agent_persist_mixin.AgentPersistMixin(settings)
    redis_client = redis.Redis.from_url("redis://localhost:6379")

    assert mixin.mark_seen("agent_x:asset", 3600) is True
    assert 0 < redis_client.ttl("agent_x:asset") <= 3600


@pytest.mark.parametrize("clean_redis_data", ["redis://localhost:6379"], indirect=True)
@pytest.mark.asyncio
@pytest.mark.docker
async def testAgentPersistMixinMarkSeen_whenKeyIsAlreadyMarked_returnFalse(
    redis_service: local_redis_service.LocalRedis,
    clean_redis_data: None,
) -> None:
    """Test mark_seen reports an already marked key."""
    del redis_service, clean_redis_data
    settings = runtime_definitions.AgentSettings(
        key="agent/ostorlab/debug", redis_url="redis://localhost:6379"
    )
    mixin = agent_persist_mixin.AgentPersistMixin(settings)

    assert mixin.mark_seen("agent_x:asset", 3600) is True
    assert mixin.mark_seen("agent_x:asset", 3600) is False


@pytest.mark.parametrize("clean_redis_data", ["redis://localhost:6379"], indirect=True)
@pytest.mark.asyncio
@pytest.mark.docker
async def testAgentPersistMixinMarkSeen_whenKeyHasExpired_returnTrue(
    redis_service: local_redis_service.LocalRedis,
    clean_redis_data: None,
) -> None:
    """Test mark_seen marks a key again once its TTL elapsed."""
    del redis_service, clean_redis_data
    settings = runtime_definitions.AgentSettings(
        key="agent/ostorlab/debug", redis_url="redis://localhost:6379"
    )
    mixin = agent_persist_mixin.AgentPersistMixin(settings)
    redis_client = redis.Redis.from_url("redis://localhost:6379")
    mixin.mark_seen("agent_x:asset", 3600)

    redis_client.expire("agent_x:asset", 0)

    assert mixin.mark_seen("agent_x:asset", 3600) is True


@pytest.mark.parametrize("redis_answer,expected", [(True, True), (None, False)])
def testAgentPersistMixinMarkSeen_whenCalled_setsKeyOnlyIfAbsentWithExpiry(
    mocker: plugin.MockerFixture, redis_answer: bool | None, expected: bool
) -> None:
    """Test mark_seen sends SET NX EX and maps the Redis answer to a boolean."""
    redis_client = mocker.MagicMock()
    redis_client.set.return_value = redis_answer
    mocker.patch("redis.Redis.from_url", return_value=redis_client)
    settings = runtime_definitions.AgentSettings(
        key="agent/ostorlab/debug", redis_url="redis://localhost:6379"
    )
    mixin = agent_persist_mixin.AgentPersistMixin(settings)

    marked = mixin.mark_seen("agent_x:asset", 3600)

    assert marked is expected
    redis_client.set.assert_called_once_with("agent_x:asset", 1, nx=True, ex=3600)


@pytest.mark.parametrize("ttl_seconds", [0, -1])
def testAgentPersistMixinMarkSeen_whenTtlIsNotPositive_raiseValueError(
    ttl_seconds: int,
) -> None:
    """Test mark_seen rejects a non-positive TTL."""
    settings = runtime_definitions.AgentSettings(
        key="agent/ostorlab/debug", redis_url="redis://localhost:6379"
    )
    mixin = agent_persist_mixin.AgentPersistMixin(settings)

    with pytest.raises(ValueError):
        mixin.mark_seen("agent_x:asset", ttl_seconds)
