"""Agent class.

The agent class is the class that all agents must inherit from to access the different features, like automated message
serialization, message receiving and sending, selector enrollment, agent health check, etc.

To use it, create a yaml file that contains the information about the agent, like name, description, license.
"""
import abc
import asyncio
import atexit
import functools
import logging
import threading
import uuid
from typing import Dict, Any

from ostorlab import exceptions
from ostorlab.agent import message as agent_message
from ostorlab.agent.mixins import agent_healthcheck_mixin
from ostorlab.agent.mixins import agent_mq_mixin
from ostorlab.runtimes import runtime

logger = logging.getLogger(__name__)


class NonListedMessageSelectorError(exceptions.OstorlabError):
    """Emit selector is not listed in the out_selector list."""


class AgentMixin(agent_mq_mixin.AgentMQMixin, agent_healthcheck_mixin.AgentHealthcheckMixin, abc.ABC):
    """Agent mixin handles all the heavy lifting.

    The agent mixin start the healthcheck service, connects the MQ and start listening to the process message.
    """

    def __init__(self,
                 agent_definition: runtime.AgentDefinition,
                 agent_instance_definition: runtime.AgentInstanceSettings
                 ) -> None:
        """Inits the agent configuration from the Yaml agent definition.

        Args:
            agent_definition: Agent definition dictating the settings of the agent, like name, in_selectors ...
            agent_instance_definition: The running instance definition dictating custom settings of the agent like bus
             URL.
        """
        self._loop = asyncio.get_event_loop()
        self.name = agent_definition.name
        self.in_selectors = agent_definition.in_selectors
        self.out_selectors = agent_definition.out_selectors
        # Arguments are defined in the agent definition, and can have a default value. The value can also be set from
        # the scan definition in the agent group. Therefore, we read both and override the value from the passed args.
        self.defined_args = agent_definition.args
        self.passed_args = agent_instance_definition.args
        self.bus_url = agent_instance_definition.bus_url
        self.bus_exchange_topic = agent_instance_definition.bus_exchange_topic
        agent_mq_mixin.AgentMQMixin.__init__(self,
                                             name=agent_definition.name,
                                             # Selectors are mapped to queue binding that listen to all
                                             # sub-routing keys.
                                             keys=[f'{s}.#' for s in self.in_selectors],
                                             url=self.bus_url,
                                             topic=self.bus_exchange_topic)
        agent_healthcheck_mixin.AgentHealthcheckMixin.__init__(self, name=agent_definition.name,
                                                               host=agent_instance_definition.healthcheck_host,
                                                               port=agent_instance_definition.healthcheck_port)

    def run(self) -> None:
        """Starts running the agent.

        Connects to the agent bus, start health check and start listening to new messages.
        """
        self.add_healthcheck(self._is_mq_healthy)
        self.add_healthcheck(self.is_healthy)
        self.start_healthcheck()
        atexit.register(functools.partial(Agent.at_exit, self))
        self._loop.run_until_complete(self.mq_init())
        logger.debug('calling start method')
        t = threading.Thread(target=self.start)
        t.start()
        t.join()
        logger.debug('calling start method done')
        try:
            if self.in_selectors is not None and len(self.in_selectors) > 0:
                logger.debug('starting mq run')
                self._loop.run_until_complete(self.mq_run())
                self._loop.run_forever()
        finally:
            logger.debug('closing MQ')
            self._loop.run_until_complete(self.mq_close())
            self._loop.close()

    def _is_mq_healthy(self) -> bool:
        """Agent health check method, to ensure MQ connection is working."""
        return self._channel_pool is not None

    @abc.abstractmethod
    def is_healthy(self) -> bool:
        """Overridable agent health check method to add custom health check logic."""
        raise NotImplementedError()

    def process_message(self, selector: str, serialized_message: bytes):
        try:
            # remove the UUID from the selector:
            selector = '.'.join(selector.split('.')[: -1])
            logger.info('%s: %s', selector, serialized_message)
            message = agent_message.Message.from_raw(selector, serialized_message)
            logger.debug('process_message: message=%s', message)
            logger.info('call process_message')
            self.process(message)
        except Exception as e:
            logger.exception('exception raised: %s', e)
        finally:
            self.process_cleanup()
            logger.debug('DONE call process_message')

    @abc.abstractmethod
    def process_cleanup(self) -> None:
        """Overridable message cleanup method to be called once process is completed or even in the case of a failure."""
        raise NotImplementedError()

    @abc.abstractmethod
    def at_exit(self) -> None:
        """Overridale at exit method to perform cleanup in the case of expected and unexpected agent termination."""
        raise NotImplementedError()

    @abc.abstractmethod
    def start(self) -> None:
        raise NotImplementedError('Missing process method implementation.')

    @abc.abstractmethod
    def process(self, message: agent_message.Message) -> None:
        raise NotImplementedError('Missing process method implementation.')

    def emit(self, selector: str, data: Dict[str, Any]) -> None:
        """

        Args:
            selector:
            data:

        Returns:

        """
        if selector not in self.out_selectors:
            logger.warning('selector not present in list of out selectors')
            # CAUTION: this check is enforced on the client-side only in certain runtimes
            raise NonListedMessageSelectorError(f'{selector} is not in {"".join(self.out_selectors)}')

        message = agent_message.Message.from_data(selector, data)
        logger.debug(f'call to send_message to %s', message)
        # A random unique UUID is added to ensure messages could be resent. Storage master ensures that a message with
        # the same selector and message body is sent only once to the bus.
        selector = f'{message.selector}.{uuid.uuid1()}'
        serialized_message = message.raw
        self.mq_send_message(selector, serialized_message)
        logger.debug('DONE call to send_message')

    @classmethod
    def main(cls) -> 'Agent':
        # read yaml file.
        # create class.
        # call the run method on it.
        raise NotImplementedError()


class Agent(AgentMixin):
    """Agent class.

    An agent can either be a message processor or standalone. Standalone agents can either be long-running or run-once.

    Message processor must implement the process method and declare a set of listen selectors. The selectors are defined
    in the YAML agent definition file.

    Standalone agents don't have any selectors to listen to and must implement its logic in the start method. Use-cases
    include input injectors, like asset injector or configuration injectors. It also includes long-running processes,
    like a proxy.

    Agents can optionally define a custom health check method `is_healthy` to inform the run time that the agent is
    operational and ensure the scan asset is not injected before the agent has completed his setup.

    The agent can also define a `process_cleanup` method that runs after every process method, even in the case of an
    exception. This can be used to perform actions, like flushing messages or status recovery.

    `at_exit` can also be defined to execute before the agent exits. This method is not 100% guaranteed before the agent
    stops. The function is not called when the program is killed by a signal not handled by Python, when a Python fatal
    internal error is detected, or when `os._exit()` is called.

    For example and more details on how to implement an agent, refer to https://docs.ostorlab.co.
    """

    def is_healthy(self) -> bool:
        """Overridable agent health check method to add custom health check logic."""
        return True

    def start(self) -> None:
        pass

    def process(self, message: agent_message.Message) -> None:
        raise NotImplementedError('Missing process method implementation.')

    def process_cleanup(self) -> None:
        """Overridale message cleanup method to be called once process is completed or even in the case of a failure."""
        pass

    def at_exit(self) -> None:
        """Overridale at exit method to perform cleanup in the case of expected and unexpected agent termination."""
        pass
