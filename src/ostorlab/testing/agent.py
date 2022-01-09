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
    mocker.patch('ostorlab.agent.mixins.agent_mq_mixin.AgentMQMixin.mq_close', return_value=None)
    mocker.patch('ostorlab.agent.agent.AgentMixin._is_mq_healthy', return_value=True)
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




