"""Tests for MockAgent class."""

import datetime
from abc import ABC

from ostorlab.runtimes import definitions as runtime_definitions
from ostorlab.agent import definitions as agent_definitions
from ostorlab.agent import agent
from ostorlab.agent.testing.mock_agent import agent_mock # pylint: disable=W0611


class StartTestAgent(agent.Agent, ABC):
    """Test Agent implementation."""


def testMockAgent_whenMessageIsSent_messagesAreAppendedtoList(agent_mock):
    definition = agent_definitions.AgentDefinition(
        name='start_test_agent',
        out_selectors=['v3.healthcheck.ping'])
    settings = runtime_definitions.AgentSettings(
        key='agent/ostorlab/start_test_agent',
        bus_url='NA',
        bus_exchange_topic='NA',
        healthcheck_port=5301)

    test_agent = StartTestAgent(definition, settings)
    test_agent.emit('v3.healthcheck.ping', {'body': f'from test agent at {datetime.datetime.now()}'})
    assert len(agent_mock) == 1
    assert agent_mock[0].selector == 'v3.healthcheck.ping'
