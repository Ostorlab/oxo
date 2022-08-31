"""Sample agents that implements the process method, listen to ping messages and sends them back."""
import datetime
import logging

from ostorlab.agent import message as agent_message
from ostorlab.agent import agent

logger = logging.getLogger(__name__)


class ProcessTestAgent(agent.Agent):
    """Custom agent implementation."""
    message = None

    def process(self, message: agent_message.Message) -> None:
        """Receives ping messages and sends new ones.

        Args:
            message: message from bus

        Returns:
            None
        """
        logger.info('received message')
        self.message = message
        self.emit('v3.healthcheck.ping', {'body': f'from test agent at {datetime.datetime.now()}'})

ProcessTestAgent.main()
