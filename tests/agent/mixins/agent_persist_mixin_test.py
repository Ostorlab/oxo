"""Tests for AgentPersistMixin module."""

import pytest
import redis

from ostorlab.agent.mixins import agent_persist_mixin
from ostorlab.runtimes import definitions as runtime_definitions


@pytest.mark.asyncio
@pytest.mark.docker
async def testAgentPersistMixin_whenSetIsAdded_setIsPersisted(mocker, redis_service):
    """Test proper storage and access of set API."""
    del mocker, redis_service
    settings = runtime_definitions.AgentSettings(key='agent/ostorlab/debug', redis_url='redis://localhost:6379')
    mixin = agent_persist_mixin.AgentPersistMixin(settings)
    _clean_redis_data(settings.redis_url)

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


@pytest.mark.asyncio
@pytest.mark.docker
async def testAgentPersistMixinDeleteKey_whenKeyExists_keyIsDeleted(mocker, redis_service):
    """Test proper storage and access of set API."""
    del mocker, redis_service
    settings = runtime_definitions.AgentSettings(key='agent/ostorlab/debug', redis_url='redis://localhost:6379')
    mixin = agent_persist_mixin.AgentPersistMixin(settings)
    _clean_redis_data(settings.redis_url)

    mixin.set_add('test1', b'A')
    mixin.delete('test1')
    assert mixin.set_members('test')  == set()


@pytest.mark.asyncio
@pytest.mark.docker
async def testAgentPersistMixin_whenHashIsAdded_hashIsPersisted(mocker, redis_service):
    """Test proper storage and access of Hash API."""
    del mocker, redis_service
    settings = runtime_definitions.AgentSettings(key='agent/ostorlab/debug', redis_url='redis://localhost:6379')
    mixin = agent_persist_mixin.AgentPersistMixin(settings)
    _clean_redis_data(settings.redis_url)

    assert mixin.hash_exists('hash_name', 'key1') is False
    mixin.hash_add('hash_name', {'key1': 'val1', 'key2': 'val2'})
    assert mixin.hash_exists('hash_name', 'key1') is True
    assert mixin.hash_get('hash_name', 'key2') == b'val2'
    assert mixin.hash_get('hash_name', 'NoneExistingKey') is None
    assert b'key1' in mixin.hash_get_all('hash_name')
    assert b'key2' in mixin.hash_get_all('hash_name')


def _clean_redis_data(redis_url: str) -> None:
    """Clean all redis data."""
    redis_client = redis.Redis.from_url(redis_url)
    keys = redis_client.keys()
    for key in keys:
        redis_client.delete(key)
