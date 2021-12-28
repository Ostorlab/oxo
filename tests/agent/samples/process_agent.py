import datetime
import logging

from ostorlab.agent import agent, message as agent_message
from ostorlab.runtimes import runtime

logger = logging.getLogger(__name__)


class ProcessTestAgent(agent.Agent):
    message = None

    def process(self, message: agent_message.Message) -> None:
        logger.info('received message')
        self.message = message
        self.emit('v3.healthcheck.ping', {'body': f'from test agent at {datetime.datetime.now()}'})


process_agent = ProcessTestAgent(
    runtime.AgentDefinition(name='process_test_agent', in_selectors=['v3.healthcheck.ping'],
                            out_selectors=['v3.healthcheck.ping']),
    runtime.AgentInstanceSettings(
        bus_url='amqp://guest:guest@localhost:5672/', bus_exchange_topic='ostorlab_test', healthcheck_port=5302))

process_agent.run()
