"""Unit test for the agent health check mixin."""
import time

import requests

from ostorlab.agent.mixins import agent_healthcheck_mixin


def testHealthcheckAgentMixin_whenHealthcheckCallbackReturnsTrue_statusReturnsOK():
    """Checks status endpoint return if status is True."""
    status_agent = agent_healthcheck_mixin.AgentHealthcheckMixin(host='127.0.1.2', port=5006)
    status_agent.add_healthcheck(lambda: True)
    status_agent.start_healthcheck()
    time.sleep(0.5)
    response = requests.get('http://127.0.1.2:5006/status')
    assert response.status_code == 200
    assert response.content == b'OK'
    status_agent.stop_healthcheck()


def testHealthcheckAgentMixin_whenHealthcheckCallbackReturnsFalse_statusReturnsNOK():
    """Checks status endpoint return if status is False."""
    status_agent = agent_healthcheck_mixin.AgentHealthcheckMixin(host='127.0.1.3', port=5006)
    status_agent.add_healthcheck(lambda: False)
    status_agent.start_healthcheck()
    time.sleep(0.5)
    response = requests.get('http://127.0.1.3:5006/status')
    assert response.status_code == 200
    assert response.content == b'NOK'
    status_agent.stop_healthcheck()


def testHealthcheckAgentMixin_whenMultipleHealthcheckCallbacksAndOneReturnsFalse_statusReturnsNOK():
    """Checks status endpoint return if status when multiple check and one returns False."""
    status_agent = agent_healthcheck_mixin.AgentHealthcheckMixin(host='127.0.1.4', port=5006)
    status_agent.add_healthcheck(lambda: False)
    status_agent.add_healthcheck(lambda: True)
    status_agent.add_healthcheck(lambda: True)
    status_agent.start_healthcheck()
    time.sleep(0.5)
    response = requests.get('http://127.0.1.4:5006/status')
    assert response.status_code == 200
    assert response.content == b'NOK'
    status_agent.stop_healthcheck()
