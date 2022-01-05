"""Tests for MockAgent class."""

import datetime
from abc import ABC

from ostorlab.runtimes import definitions as runtime_definitions
from ostorlab.agent import definitions as agent_definitions
from ostorlab.agent.testing import mock_agent
from ostorlab.agent import agent


class StartTestAgent(agent.Agent, ABC):
    """Test Agent implementation."""


def testMockAgent_whenMessageIsSent_messagesAreAppendedtoList():
    definition = agent_definitions.AgentDefinition(
        name='start_test_agent',
        out_selectors=['v3.healthcheck.ping'])
    settings = runtime_definitions.AgentSettings(
        key='agent/ostorlab/start_test_agent',
        bus_url='NA',
        bus_exchange_topic='NA',
        healthcheck_port=5301)

    test_agent = mock_agent.start_agent(StartTestAgent, definition, settings)
    test_agent.emit('v3.healthcheck.ping', {'body': f'from test agent at {datetime.datetime.now()}'})
    assert len(test_agent.emit_message_with_selector_queue) == 1
    assert test_agent.emit_message_with_selector_queue[0].selector == 'v3.healthcheck.ping'
