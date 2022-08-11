"""Unit tests for OpenTelemtryMixin module."""
from typing import Any, Dict
import json

from opentelemetry.sdk.trace import export as sdk_export

from ostorlab.agent import agent
from ostorlab.agent import definitions as agent_definitions
from ostorlab.runtimes import definitions as runtime_definitions
from ostorlab.agent import message as agent_message


class TestAgent(agent.Agent):
    """Helper class to test OpenTelemtry mixin implementation."""
    def process(self, message: agent_message.Message) -> None:
        pass


def testOpenTelemtryMixin_whenEmitMessage_shouldTraceMessage(agent_mock):
    """Unit test for the OpenTelemtry Mixin, ensure the correct exporter has been used and trace span has been sent."""
    agent_definition = agent_definitions.AgentDefinition(
        name='some_name',
        out_selectors=['v3.report.vulnerability'])
    agent_settings = runtime_definitions.AgentSettings(
        key='some_key',
        tracing_collector_url='console')
    test_agent = TestAgent(
        agent_definition=agent_definition,
        agent_settings=agent_settings)

    test_agent.emit('v3.report.vulnerability', {
        'title': 'some_title',
        'technical_detail': 'some_details',
        'risk_rating': 'MEDIUM'
    })
