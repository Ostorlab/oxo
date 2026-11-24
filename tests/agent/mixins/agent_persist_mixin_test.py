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


_REDIS_URL = "redis://localhost:6379"
_DAY = 24 * 60 * 60
_NOW = 1_800_000_000.0


def _mixin() -> agent_persist_mixin.AgentPersistMixin:
    settings = runtime_definitions.AgentSettings(
        key="agent/ostorlab/debug", redis_url=_REDIS_URL
    )
    return agent_persist_mixin.AgentPersistMixin(settings)


@pytest.mark.parametrize("clean_redis_data", [_REDIS_URL], indirect=True)
@pytest.mark.docker
def testAgentPersistMixinSet_whenMembersAreAddedAtDifferentTimes_eachIsForgottenOnItsOwn(
    mocker: plugin.MockerFixture,
    redis_service: local_redis_service.LocalRedis,
    clean_redis_data: None,
) -> None:
    """A member leaves the set 7 days after it was added, the members added later stay."""
    del redis_service, clean_redis_data
    clock = mocker.patch("time.time", return_value=_NOW)
    mixin = _mixin()
    mixin.set_add("seen", "a.com")
    clock.return_value = _NOW + 6 * _DAY
    mixin.set_add("seen", "b.com")
    assert mixin.set_is_member("seen", "a.com") is True

    clock.return_value = _NOW + 7 * _DAY

    assert mixin.set_is_member("seen", "a.com") is False
    assert mixin.set_is_member("seen", "b.com") is True
    assert mixin.set_len("seen") == 1
    assert mixin.set_members("seen") == {b"b.com"}
    assert mixin.set_add("seen", "a.com") is True
    assert mixin.set_add("seen", "b.com") is False


@pytest.mark.parametrize("clean_redis_data", [_REDIS_URL], indirect=True)
@pytest.mark.docker
def testAgentPersistMixinSetAdd_whenMemberIsStillKnown_keepsItsExpiryTime(
    mocker: plugin.MockerFixture,
    redis_service: local_redis_service.LocalRedis,
    clean_redis_data: None,
) -> None:
    """Adding a known member again does not make it stay longer."""
    del redis_service, clean_redis_data
    clock = mocker.patch("time.time", return_value=_NOW)
    mixin = _mixin()
    mixin.set_add("seen", "a.com")
    clock.return_value = _NOW + 6 * _DAY
    mixin.set_add("seen", "a.com")

    clock.return_value = _NOW + 7 * _DAY

    assert mixin.set_is_member("seen", "a.com") is False


@pytest.mark.parametrize("clean_redis_data", [_REDIS_URL], indirect=True)
@pytest.mark.docker
def testAgentPersistMixinAddIpNetwork_whenNetworkTtlPasses_addsItAgain(
    mocker: plugin.MockerFixture,
    redis_service: local_redis_service.LocalRedis,
    clean_redis_data: None,
) -> None:
    """A network is new again once its time passes."""
    del redis_service, clean_redis_data
    clock = mocker.patch("time.time", return_value=_NOW)
    mixin = _mixin()
    network = ipaddress.ip_network("8.8.8.0/24")
    assert mixin.add_ip_network("seen_ip", network) is True
    assert mixin.add_ip_network("seen_ip", network) is False

    clock.return_value = _NOW + 7 * _DAY

    assert mixin.ip_network_exists("seen_ip", network) is False
    assert mixin.add_ip_network("seen_ip", network) is True


@pytest.mark.parametrize("clean_redis_data", [_REDIS_URL], indirect=True)
@pytest.mark.docker
def testAgentPersistMixinSet_always_keepsThePlainRedisSet(
    mocker: plugin.MockerFixture,
    redis_service: local_redis_service.LocalRedis,
    clean_redis_data: None,
) -> None:
    """A client that reads or writes the set without the mixin keeps working, its members do not expire."""
    del redis_service, clean_redis_data
    clock = mocker.patch("time.time", return_value=_NOW)
    client = redis.Redis.from_url(_REDIS_URL)
    mixin = _mixin()
    mixin.set_add("seen", "a.com")
    client.sadd("seen", "raw.com")

    assert mixin.value_type("seen") == "set"
    assert client.sismember("seen", "a.com") == 1
    assert mixin.set_is_member("seen", "raw.com") is True

    clock.return_value = _NOW + 7 * _DAY

    assert mixin.set_members("seen") == {b"raw.com"}
    assert client.smembers("seen") == {b"raw.com"}


@pytest.mark.parametrize("clean_redis_data", [_REDIS_URL], indirect=True)
@pytest.mark.docker
def testAgentPersistMixinDelete_whenKeyIsSet_forgetsTheExpiryTimesOfItsMembers(
    mocker: plugin.MockerFixture,
    redis_service: local_redis_service.LocalRedis,
    clean_redis_data: None,
) -> None:
    """A member added again after the set was deleted stays 7 days from that moment."""
    del redis_service, clean_redis_data
    clock = mocker.patch("time.time", return_value=_NOW)
    mixin = _mixin()
    mixin.set_add("seen", "a.com")
    clock.return_value = _NOW + 6 * _DAY
    mixin.delete("seen")
    mixin.set_add("seen", "a.com")

    clock.return_value = _NOW + 7 * _DAY

    assert set(redis.Redis.from_url(_REDIS_URL).keys()) == {
        b"seen",
        b"seen:expires_at",
    }
    assert mixin.set_is_member("seen", "a.com") is True


@pytest.mark.parametrize("clean_redis_data", [_REDIS_URL], indirect=True)
@pytest.mark.docker
def testAgentPersistMixinAdd_always_storesTheValueForSevenDays(
    redis_service: local_redis_service.LocalRedis,
    clean_redis_data: None,
) -> None:
    """A value is given an expiry by Redis, so that it does not stay forever."""
    del redis_service, clean_redis_data
    mixin = _mixin()

    mixin.add("key", b"value")

    assert mixin.get("key") == b"value"
    assert 7 * _DAY - 60 < redis.Redis.from_url(_REDIS_URL).ttl("key") <= 7 * _DAY
