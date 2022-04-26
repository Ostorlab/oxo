"""Tests for AgentPersistMixin module."""

import pytest

from ostorlab.agent.mixins import agent_persist_mixin
from ostorlab.runtimes import definitions as runtime_definitions


@pytest.mark.asyncio
@pytest.mark.docker
async def testAgentPersistMixin_whenSetIsAdded_setIsPersisted(mocker, redis_service):
    """Test proper storage and access of set API."""
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

