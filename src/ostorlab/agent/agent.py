"""Agent class.

The agent class is the class that all agents must inherit from to access the different features, like automated message
serialization, message receiving and sending, selector enrollment, agent health check, etc.

To use it, create a yaml file that contains the information about the agent, like name, description, license.
"""
import abc
import asyncio
import logging
import os
import uuid
from typing import Dict, Any, List

from ostorlab.agent import message as agent_message
from ostorlab.agent.mixins import agent_healthcheck_mixin
from ostorlab.runtimes import runtime

logger = logging.getLogger(__name__)


class Agent(agent_healthcheck_mixin.AgentHealthcheckMixin, abc.ABC):
    """Agent class exposes automated selector enrollment, agent health check, automated message serialisation."""

    name: str
    in_selectors: List[str]
    out_selectors: List[str]
    # TODO(alaeddine): add better type definition for args.
    args: List
    bus_url: str
    bus_vhost: str
    bus_exchange: str
    bus_username: str
    bus_password: str

    def __init__(self, agent_definition: runtime.AgentDefinition) -> None:
        """Inits the agent configuration from the Yaml agent definition.

        Args:
            agent_definition: Yaml agent definition dictating the settings of the agent.
        """
        self.name = agent_definition.name
        self.in_selectors = agent_definition.in_selectors
        self.out_selectors = agent_definition.out_selectors
        self.args = agent_definition.args
        self.bus_url = os.environ['BUS_URL']
        self.bus_vhost = os.environ['BUS_VHOST']
        self.bus_exchange = os.environ['BUS_EXCHANGE']
        self.bus_username = os.environ['BUS_USERNAME']
        self.bus_password = os.environ['BUS_PASS']
        # TODO: MQ class
        agent_healthcheck_mixin.AgentHealthcheckMixin.__init__(self, name=agent_definition.name)

    def run(self) -> None:
        """Starts running the agent. Connects to the agent bus, start health check and start listening for new messages.

        Returns:
            None
        """
        self.add_healthcheck(self._is_mq_healthy)
        self.add_healthcheck(self.is_healthy)
        self.start_healthcheck()
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(self.mq_run())
        else:
            loop.run_until_complete(self.mq_run())
            try:
                loop.run_forever()
            finally:
                loop.run_until_complete(self.mq_close())
                self.stop_healthcheck()

    def _is_mq_health(self) -> bool:
        """Agent health check method, to ensure MQ connection is working."""
        raise NotImplementedError()

    def is_healthy(self) -> bool:
        """Overridable agent health check method to add custom health check logic."""
        return True

    def _process_message(self, selector, serialized_message):
        self._message_selector = None

        try:
            message = ScanAgent.deserialize(selector, serialized_message)
            logger.debug('process_message: message=%s', message)
            logger.info('call process_message')
            self._message_selector = selector.split('.')[1:-1]

            self.process(message)
        except Exception as e:
            logger.exception('exception raised by %s: %s', self._name_, e)
        finally:
            self._process_message_cleanup()

    def _process_message_cleanup(self) -> None:
        # flush remaining vulnerabilities and fingerprints from queue.
        logger.debug('DONE call process_message')

    @abc.abstractmethod
    def process(self, message: agent_message.Message) -> None:
        raise NotImplementedError('Missing process method implementation.')

    def emit(self, selector: str, data: Dict[str, Any]) -> None:
        # check the selector is in the list of out_selectors.

        message = agent_message.Message.from_data(selector, data)

        logger.debug(f'call to send_message to %s', message)
        # A random unique UUID is added to ensure messages could be resent. Storage master ensures that a message with
        # the same selector and message body is sent only once to the bus.
        selector = message.selector + '.' + str(uuid.uuid1())
        serialized_message = message.data

        self.mq_send_message(selector, serialized_message)
        logger.debug('DONE call to send_message')