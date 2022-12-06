"""Tests for MockAgent class."""

import datetime
from abc import ABC

from ostorlab.runtimes import definitions as runtime_definitions
from ostorlab.agent import agent, definitions as agent_definitions
from ostorlab.agent.mixins import agent_persist_mixin


class StartTestAgent(agent.Agent, ABC):
    """Test Agent implementation."""


class PersistTestAgent(agent.Agent, agent_persist_mixin.AgentPersistMixin):
    def __init__(
        self,
        agent_definition: agent_definitions.AgentDefinition,
        agent_settings: runtime_definitions.AgentSettings,
    ) -> None:
        agent.Agent.__init__(self, agent_definition, agent_settings)
        agent_persist_mixin.AgentPersistMixin.__init__(self, agent_settings)


def testMockAgent_whenMessageIsSent_messagesAreAppendedtoList(agent_mock):
    """Test collection of message by agent mock."""
    definition = agent_definitions.AgentDefinition(
        name="start_test_agent", out_selectors=["v3.healthcheck.ping"]
    )
    settings = runtime_definitions.AgentSettings(
        key="agent/ostorlab/start_test_agent",
        bus_url="NA",
        bus_exchange_topic="NA",
        healthcheck_port=5301,
    )

    test_agent = StartTestAgent(definition, settings)
    test_agent.emit(
        "v3.healthcheck.ping", {"body": f"from test agent at {datetime.datetime.now()}"}
    )
    assert len(agent_mock) == 1
    assert agent_mock[0].selector == "v3.healthcheck.ping"


def testMockPersistAgent_whensetMethodsAreCalled_stateIsPersistedByMock(
    agent_mock, agent_persist_mock
):
    """Test collection of values by agent persist mock."""
    definition = agent_definitions.AgentDefinition(
        name="start_test_agent", out_selectors=["v3.healthcheck.ping"]
    )
    settings = runtime_definitions.AgentSettings(
        key="agent/ostorlab/start_test_agent",
        bus_url="NA",
        bus_exchange_topic="NA",
        healthcheck_port=5301,
        redis_url="redis://redis",
    )

    test_agent = PersistTestAgent(definition, settings)
    assert test_agent.set_is_member("test", "1") is False
    assert test_agent.set_add("test", "1") is True
    assert test_agent.set_is_member("test", "1") is True
    assert agent_persist_mock == {"test": {"1"}}
