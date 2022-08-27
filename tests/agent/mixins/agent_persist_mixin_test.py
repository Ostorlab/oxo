"""Tests for AgentPersistMixin module."""
import ipaddress

import pytest

from ostorlab.agent.mixins import agent_persist_mixin
from ostorlab.runtimes import definitions as runtime_definitions


@pytest.mark.parametrize('clean_redis_data', ['redis://localhost:6379'], indirect=True)
@pytest.mark.asyncio
@pytest.mark.docker
async def testAgentPersistMixin_whenSetIsAdded_setIsPersisted(mocker, redis_service, clean_redis_data):
    """Test proper storage and access of set API."""
    del mocker, redis_service, clean_redis_data
    settings = runtime_definitions.AgentSettings(key='agent/ostorlab/debug', redis_url='redis://localhost:6379')
    mixin = agent_persist_mixin.AgentPersistMixin(settings)

    assert mixin.set_is_member('test', 'A') is False
    mixin.set_add('test', b'A')
    mixin.set_add('test', 'B')
    assert mixin.set_is_member('test', 'A') is True
    assert mixin.set_is_member('test', 'B') is True
    assert mixin.set_is_member('test', 'C') is False
    assert mixin.set_len('test') == 2
    assert mixin.set_members('test') == {b'A', b'B'}
    mixin.add('myKey', b'myVal')
    assert mixin.get('myKey') == b'myVal'
    assert mixin.get('myKey1') is None
    assert mixin.value_type('test') == 'set'
    assert mixin.value_type('myKey') == 'string'
    assert mixin.value_type('myKey1') == 'none'


@pytest.mark.parametrize('clean_redis_data', ['redis://localhost:6379'], indirect=True)
@pytest.mark.asyncio
@pytest.mark.docker
async def testAgentPersistMixinDeleteKey_whenKeyExists_keyIsDeleted(mocker, redis_service, clean_redis_data):
    """Test proper storage and access of set API."""
    del mocker, redis_service, clean_redis_data
    settings = runtime_definitions.AgentSettings(key='agent/ostorlab/debug', redis_url='redis://localhost:6379')
    mixin = agent_persist_mixin.AgentPersistMixin(settings)

    mixin.set_add('test1', b'A')
    mixin.delete('test1')
    assert mixin.set_members('test') == set()


@pytest.mark.parametrize('clean_redis_data', ['redis://localhost:6379'], indirect=True)
@pytest.mark.asyncio
@pytest.mark.docker
async def testAgentPersistMixin_whenHashIsAdded_hashIsPersisted(mocker, redis_service, clean_redis_data):
    """Test proper storage and access of Hash API."""
    del mocker, redis_service, clean_redis_data
    settings = runtime_definitions.AgentSettings(key='agent/ostorlab/debug', redis_url='redis://localhost:6379')
    mixin = agent_persist_mixin.AgentPersistMixin(settings)

    assert mixin.hash_exists('hash_name', 'key1') is False
    mixin.hash_add('hash_name', {'key1': 'val1', 'key2': 'val2'})
    assert mixin.hash_exists('hash_name', 'key1') is True
    assert mixin.hash_get('hash_name', 'key2') == b'val2'
    assert mixin.hash_get('hash_name', 'NoneExistingKey') is None
    assert b'key1' in mixin.hash_get_all('hash_name')
    assert b'key2' in mixin.hash_get_all('hash_name')


@pytest.mark.parametrize('clean_redis_data', ['redis://localhost:6379'], indirect=True)
@pytest.mark.asyncio
@pytest.mark.docker
async def testAgentPersistMixinCheckIpRangeExist_whenIpRangeIsCovered_returnTrue(mocker, redis_service, clean_redis_data):
    """Test mixin.add_ip_network returns True if ip_range is added and False if the ip_range
    or one of his supersets already exits """
    del mocker, redis_service, clean_redis_data
    settings = runtime_definitions.AgentSettings(key='agent/ostorlab/debug', redis_url='redis://localhost:6379')
    mixin = agent_persist_mixin.AgentPersistMixin(settings)

    assert mixin.add_ip_network('test_ip', ipaddress.ip_network('8.8.8.0/23')) is True
    assert mixin.add_ip_network('test_ip', ipaddress.ip_network('8.8.8.0/24')) is False
    assert mixin.add_ip_network('test_ip', ipaddress.ip_network('8.8.8.0/23')) is False
    assert mixin.add_ip_network('test_ip', ipaddress.ip_network('8.8.8.0/24')) is False
    assert mixin.add_ip_network('test_ip', ipaddress.ip_network('8.8.8.0/31')) is False
    assert mixin.add_ip_network('test_ip', ipaddress.ip_network('8.8.8.0/22')) is True
    assert mixin.add_ip_network('test_ip', ipaddress.ip_network('10.10.10.0/23')) is True
    assert mixin.add_ip_network('test_ip', ipaddress.ip_network('10.10.10.0/28')) is False

@pytest.mark.parametrize('clean_redis_data', ['redis://localhost:6379'], indirect=True)
@pytest.mark.asyncio
@pytest.mark.docker
async def testAgentPersistMixinCheckIpRangeExist_withCallableKey_returnTrue(mocker, redis_service, clean_redis_data):
    """Test mixin.add_ip_network returns True if ip_range is added and False if the ip_range
    or one of his supersets already exits """
    del mocker, redis_service, clean_redis_data
    settings = runtime_definitions.AgentSettings(key='agent/ostorlab/debug', redis_url='redis://localhost:6379')
    mixin = agent_persist_mixin.AgentPersistMixin(settings)

    assert mixin.add_ip_network('test_ip', ipaddress.ip_network('8.8.8.0/23'), lambda net: f'X_{net}_Y') is True
    assert mixin.add_ip_network('test_ip', ipaddress.ip_network('8.8.8.0/24'), lambda net: f'X_{net}_Y') is False
    assert mixin.add_ip_network('test_ip', ipaddress.ip_network('8.8.8.0/23'), lambda net: f'X_{net}_Y') is False
    assert mixin.add_ip_network('test_ip', ipaddress.ip_network('8.8.8.0/24'), lambda net: f'X_{net}_Y') is False
    assert mixin.add_ip_network('test_ip', ipaddress.ip_network('8.8.8.0/31'), lambda net: f'X_{net}_Y') is False
    assert mixin.add_ip_network('test_ip', ipaddress.ip_network('8.8.8.0/22'), lambda net: f'X_{net}_Y') is True
    assert mixin.add_ip_network('test_ip', ipaddress.ip_network('10.10.10.0/23'), lambda net: f'X_{net}_Y') is True
    assert mixin.add_ip_network('test_ip', ipaddress.ip_network('10.10.10.0/28'), lambda net: f'X_{net}_Y') is False

