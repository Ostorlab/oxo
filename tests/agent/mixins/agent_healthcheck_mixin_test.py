"""Unit test for the agent health check mixin."""

import time

import httpx

from ostorlab.agent.mixins import agent_healthcheck_mixin


def testHealthcheckAgentMixin_whenHealthcheckCallbackReturnsTrue_statusReturnsOK() -> (
    None
):
    """Checks status endpoint return if status is True."""
    status_agent = agent_healthcheck_mixin.AgentHealthcheckMixin(
        host="127.0.1.2", port=5006
    )
    status_agent.add_healthcheck(lambda: True)
    status_agent.start_healthcheck()
    time.sleep(0.5)
    response = httpx.get("http://127.0.1.2:5006/status", timeout=10)
    assert response.status_code == 200
    assert response.content == b"OK"
    status_agent.stop_healthcheck()


def testHealthcheckAgentMixin_whenHealthcheckCallbackReturnsFalse_statusReturnsNOK() -> (
    None
):
    """Checks status endpoint return if status is False."""
    status_agent = agent_healthcheck_mixin.AgentHealthcheckMixin(
        host="127.0.1.3", port=5006
    )
    status_agent.add_healthcheck(lambda: False)
    status_agent.start_healthcheck()
    time.sleep(0.5)
    response = httpx.get("http://127.0.1.3:5006/status", timeout=10)
    assert response.status_code == 200
    assert response.content == b"NOK"
    status_agent.stop_healthcheck()


def testHealthcheckAgentMixin_whenMultipleHealthcheckCallbacksAndOneReturnsFalse_statusReturnsNOK() -> (
    None
):
    """Checks status endpoint return if status when multiple check and one returns False."""
    status_agent = agent_healthcheck_mixin.AgentHealthcheckMixin(
        host="127.0.1.4", port=5006
    )
    status_agent.add_healthcheck(lambda: False)
    status_agent.add_healthcheck(lambda: True)
    status_agent.add_healthcheck(lambda: True)
    status_agent.start_healthcheck()
    time.sleep(0.5)
    response = httpx.get("http://127.0.1.4:5006/status", timeout=10)
    assert response.status_code == 200
    assert response.content == b"NOK"
    status_agent.stop_healthcheck()


def testHealthcheckAgentMixin_whenIdleCheckReturnsTrue_idleReturns1() -> None:
    """The /idle endpoint answers 1 while the agent processes no message."""
    idle_agent = agent_healthcheck_mixin.AgentHealthcheckMixin(
        host="127.0.1.5", port=5006
    )
    idle_agent.set_idle_check(lambda: True)
    idle_agent.start_healthcheck()
    time.sleep(0.5)
    response = httpx.get("http://127.0.1.5:5006/idle", timeout=10)
    assert response.status_code == 200
    assert response.content == b"1"
    idle_agent.stop_healthcheck()


def testHealthcheckAgentMixin_whenIdleCheckReturnsFalse_idleReturns0() -> None:
    """The /idle endpoint answers 0 while the agent processes a message."""
    busy_agent = agent_healthcheck_mixin.AgentHealthcheckMixin(
        host="127.0.1.6", port=5006
    )
    busy_agent.set_idle_check(lambda: False)
    busy_agent.start_healthcheck()
    time.sleep(0.5)
    response = httpx.get("http://127.0.1.6:5006/idle", timeout=10)
    assert response.status_code == 200
    assert response.content == b"0"
    busy_agent.stop_healthcheck()


def testHealthcheckAgentMixin_whenNoIdleCheckIsSet_idleReturns404() -> None:
    """Without an idle check the activity is unknown, /idle answers 404 like an agent of an older SDK."""
    unknown_agent = agent_healthcheck_mixin.AgentHealthcheckMixin(
        host="127.0.1.7", port=5006
    )
    unknown_agent.add_healthcheck(lambda: True)
    unknown_agent.start_healthcheck()
    time.sleep(0.5)
    response = httpx.get("http://127.0.1.7:5006/idle", timeout=10)
    assert response.status_code == 404
    unknown_agent.stop_healthcheck()


def testHealthcheckAgentMixin_whenActivityChanges_idleFollowsEachRequest() -> None:
    """The idle check is evaluated on every request, not once when it is set."""
    activity = {"idle": True}
    changing_agent = agent_healthcheck_mixin.AgentHealthcheckMixin(
        host="127.0.1.8", port=5006
    )
    changing_agent.set_idle_check(lambda: activity["idle"])
    changing_agent.start_healthcheck()
    time.sleep(0.5)
    first = httpx.get("http://127.0.1.8:5006/idle", timeout=10)
    activity["idle"] = False
    second = httpx.get("http://127.0.1.8:5006/idle", timeout=10)
    activity["idle"] = True
    third = httpx.get("http://127.0.1.8:5006/idle", timeout=10)
    assert [first.content, second.content, third.content] == [b"1", b"0", b"1"]
    changing_agent.stop_healthcheck()


def testHealthcheckAgentMixin_whenIdleCheckIsSet_statusIsUnchanged() -> None:
    """/status keeps answering from the health checks alone, a busy agent stays healthy."""
    status_agent = agent_healthcheck_mixin.AgentHealthcheckMixin(
        host="127.0.1.9", port=5006
    )
    status_agent.add_healthcheck(lambda: True)
    status_agent.set_idle_check(lambda: False)
    status_agent.start_healthcheck()
    time.sleep(0.5)
    status = httpx.get("http://127.0.1.9:5006/status", timeout=10)
    idle = httpx.get("http://127.0.1.9:5006/idle", timeout=10)
    assert status.status_code == 200
    assert status.content == b"OK"
    assert idle.content == b"0"
    status_agent.stop_healthcheck()
