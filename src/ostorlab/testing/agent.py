"""mock agent implements the required methods to test the agent's behavior without using external components."""
import pytest

from typing import List

from ostorlab.agent import message as msg


@pytest.fixture(scope='function')
def agent_mock(mocker):
    """This fixtures patches all the Agent components and returns the list of messages emitted """
    emitted_messages: List[msg.Message] = []
    mocker.patch('ostorlab.agent.mixins.agent_mq_mixin.AgentMQMixin.mq_init', return_value=None)
    mocker.patch('ostorlab.agent.mixins.agent_mq_mixin.AgentMQMixin.mq_run', return_value=None)
    mocker.patch(
        'ostorlab.agent.mixins.agent_healthcheck_mixin.AgentHealthcheckMixin.start_healthcheck',
        return_value=None
    )
    mocker.patch(
        'ostorlab.agent.mixins.agent_healthcheck_mixin.AgentHealthcheckMixin.add_healthcheck',
        return_value=None
    )
    mocker.patch(
        'ostorlab.agent.mixins.agent_healthcheck_mixin.AgentHealthcheckMixin.__init__',
        return_value=None
    )

    def mq_send_message(key, message):
        # we need to remove the last part of the key f'{selector}.{uuid.uuid1()}'
        agent_message = msg.Message.from_raw('.'.join(key.split('.')[:-1]), message)
        emitted_messages.append(agent_message)

    mocker.patch('ostorlab.agent.mixins.agent_mq_mixin.AgentMQMixin.mq_send_message', side_effect=mq_send_message)
    yield emitted_messages
    emitted_messages = []


@pytest.fixture(scope='function')
def agent_persist_mock(mocker):
    """This fixtures patches the Agent persist component and returns the list storage state"""
    storage = {}

    def _set_is_member(key, value):
        """Check values are present in the storage dict."""
        return key in storage and value in storage[key]

    def _set_add(key, value):
        """Add members to the storage dict and emulate return value."""
        if _set_is_member(key, value):
            return False
        else:
            storage.setdefault(key, set()).add(value)
            return True

    mocker.patch('ostorlab.agent.mixins.agent_persist_mixin.AgentPersistMixin.set_add',
                 side_effect=_set_add)
    mocker.patch('ostorlab.agent.mixins.agent_persist_mixin.AgentPersistMixin.set_is_member',
                 side_effect=_set_is_member)
    yield storage
    storage = {}






