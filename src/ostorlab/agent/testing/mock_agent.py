"""mock agent implements the required methods to test the agent's behaviors without using external components."""
import pytest

from typing import Any, List, Dict

from ostorlab.agent import message



@pytest.fixture
def agent_mock(mocker):
    """This fixtures patches all the Agent components and returns the list of messaged emitted """
    emit_message_with_selector_queue: List[message.Message] = []
    mocker.patch('ostorlab.agent.mixins.agent_mq_mixin.AgentMQMixin.mq_init', return_value=None)
    mocker.patch('ostorlab.agent.mixins.agent_mq_mixin.AgentMQMixin.mq_run', return_value=None)
    mocker.patch('ostorlab.agent.mixins.agent_mq_mixin.AgentMQMixin.mq_close', return_value=None)
    mocker.patch('ostorlab.agent.agent.AgentMixin._is_mq_healthy', return_value=True)

    def emit_message(selector: str, data: Dict[str, Any]):
        agent_message = message.Message.from_data(selector, data)
        emit_message_with_selector_queue.append(agent_message)

    mocker.patch('ostorlab.agent.agent.AgentMixin.emit', side_effect=emit_message)
    yield emit_message_with_selector_queue




