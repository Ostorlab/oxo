import datetime
import logging
import multiprocessing as mp
import time

import pytest

from ostorlab.agent import agent, message as agent_message
from ostorlab.runtimes import runtime

logger = logging.getLogger(__name__)


@pytest.mark.timeout(60)
@pytest.mark.docker
def testAgent_whenAnAgentSendAMessageFromStartAgent_listeningToMessageReceivesIt(mq_service):
    """The setup of this test seems complicated, but it is the most robust implementation iteration.

    The test also tests for many things at the same time, like start and process lifecycle, message emit and message
    serialization.

    The test defines two agent, a start-only agent that sends a ping and a process-only agent the listens for pings.
    The process agent is start first as a dedicated process to start listening. Once a message is received, a
    multiprocess event is set to True.

    After 1 seconds, all processes are terminated and the event is checked.
    """
    mp_event = mp.Event()

    class StartTestAgent(agent.Agent):
        def start(self) -> None:
            self.emit('v3.healthcheck.ping', {'body': f'from test agent at {datetime.datetime.now()}'})

    class ProcessTestAgent(agent.Agent):
        def process(self, message: agent_message.Message) -> None:
            logger.info('process is called, setting event')
            mp_event.set()

    start_agent = StartTestAgent(
        runtime.AgentDefinition(name='start_test_agent', out_selectors=['v3.healthcheck.ping']),
        runtime.AgentInstanceSettings(
            bus_url='amqp://guest:guest@localhost:5672/', bus_exchange_topic='ostorlab_test',
            healthcheck_port=5301,
        ))
    process_agent = ProcessTestAgent(
        runtime.AgentDefinition(name='process_test_agent', in_selectors=['v3.healthcheck.ping']),
        runtime.AgentInstanceSettings(
            bus_url='amqp://guest:guest@localhost:5672/', bus_exchange_topic='ostorlab_test', healthcheck_port=5302))

    mp_event.clear()
    process_agent_t = mp.Process(target=process_agent.run)
    process_agent_t.start()
    time.sleep(1)
    start_agent_t = mp.Process(target=start_agent.run)
    start_agent_t.start()
    time.sleep(1)
    process_agent_t.terminate()
    start_agent_t.terminate()

    assert mp_event.is_set() is True
