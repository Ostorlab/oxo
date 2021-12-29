"""Agent class.

All agents should inherit from the agent class to access the different features, like automated message
serialization, message receiving and sending, selector enrollment, agent health check, etc.

To use it, check out documentations at https://docs.ostorlab.co/.
"""
import abc
import argparse
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
from ostorlab.runtimes import definitions

logger = logging.getLogger(__name__)


class NonListedMessageSelectorError(exceptions.OstorlabError):
    """Emit selector is not listed in the out_selector list."""


class AgentMixin(agent_mq_mixin.AgentMQMixin, agent_healthcheck_mixin.AgentHealthcheckMixin, abc.ABC):
    """Agent mixin handles all the heavy lifting.

    The agent mixin start the healthcheck service, connects the MQ and start listening to the process message.
    """

    def __init__(self,
                 agent_definition: definitions.AgentDefinition,
                 agent_instance_definition: definitions.AgentInstanceSettings
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
        # This is call in a thread to avoid blocking calls from affecting the MQ heartbeat running on the main thread.
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
            logger.debug('closing bus and loop')
            self._loop.run_until_complete(self.mq_close())
            self._loop.close()

    def _is_mq_healthy(self) -> bool:
        """Agent health check method, to ensure MQ connection is working."""
        return self._channel_pool is not None

    @abc.abstractmethod
    def is_healthy(self) -> bool:
        """Overridable agent health check method to add custom health check logic.

        Returns:
            bool to indicate if the agent is healthy of not.
        """
        raise NotImplementedError()

    def process_message(self, selector: str, message: bytes) -> None:
        """Processes raw message received from BS.

        Args:
            selector: destination selector with full path, including UUID set by default.
            message: raw bytes message.

        Returns:
            None
        """
        try:
            # remove the UUID from the selector:
            selector = '.'.join(selector.split('.')[: -1])
            message = agent_message.Message.from_raw(selector, message)
            logger.debug('call to process with message=%s', message)
            self.process(message)
        # pylint: disable=W0703
        except Exception as e:
            logger.exception('exception raised: %s', e)
        finally:
            self.process_cleanup()
            logger.debug('done call to process message')

    @abc.abstractmethod
    def process_cleanup(self) -> None:
        """Overridable message cleanup method to be called once process is completed or even in the case of a failure.

        Returns:
            None
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def at_exit(self) -> None:
        """Overridable at exit method to perform cleanup in the case of expected and unexpected agent termination.

        Returns:

        """
        raise NotImplementedError()

    @abc.abstractmethod
    def start(self) -> None:
        """Overridable agent start to implement one-off or long-processing non-receiving agents.

        Returns:
            None
        """
        raise NotImplementedError('Missing process method implementation.')

    @abc.abstractmethod
    def process(self, message: agent_message.Message) -> None:
        """Overridable message processing method.

        Args:
            message: message received from with selector and data.

        Returns:
            None
        """
        raise NotImplementedError('Missing process method implementation.')

    def emit(self, selector: str, data: Dict[str, Any]) -> None:
        """Sends a message to all listening agents on the specified selector.

        Args:
            selector: target selector.
            data: message data to be serialized.

        Returns:
            None
        """
        if selector not in self.out_selectors:
            logger.error('selector not present in list of out selectors')
            # CAUTION: this check is enforced on the client-side only in certain runtimes
            raise NonListedMessageSelectorError(f'{selector} is not in {"".join(self.out_selectors)}')

        message = agent_message.Message.from_data(selector, data)
        logger.debug('call to send message with %s', message)
        # A random unique UUID is added to ensure messages could be resent. Storage master ensures that a message with
        # the same selector and message body is sent only once to the bus.
        selector = f'{message.selector}.{uuid.uuid1()}'
        serialized_message = message.raw
        self.mq_send_message(selector, serialized_message)
        logger.debug('done call to send_message')

    @classmethod
    def main(cls) -> None:
        """Prepares the agents class by reading and settings all the parameters passed from runtimes.

        Returns:
            Agent instance.
        """
        parser = argparse.ArgumentParser()
        parser.add_argument('-f', '--file', help='Agent YAML definition file.')
        parser.add_argument('-p', '--proto', help='Agent binary proto settings.')
        args = parser.parse_args()
        logger.info('running agent with definition %s and proto %s', args.file, args.proto)
        agent_definition = definitions.AgentDefinition.from_yaml(args.file)
        agent_settings = definitions.AgentInstanceSettings.from_proto(args.proto)
        instance = cls(agent_definition=agent_definition, agent_instance_definition=agent_settings)
        instance.run()


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
        """Overridable agent health check method to add custom health check logic.

        Returns:
            bool to indicate if the agent is healthy or not.
        """
        return True

    def start(self) -> None:
        """Overridable agent start to implement one-off or long-processing non-receiving agents.

        Returns:
            None
        """
        pass

    def process(self, message: agent_message.Message) -> None:
        """Overridable message processing method.

        Args:
            message: message received from with selector and data.

        Returns:
            None
        """
        raise NotImplementedError('Missing process method implementation.')

    def process_cleanup(self) -> None:
        """Overridable message cleanup method to be called once process is completed or even in the case of a failure.

        Returns:
            None
        """
        pass

    def at_exit(self) -> None:
        """Overridable at exit method to perform cleanup in the case of expected and unexpected agent termination.

        Returns:
            None
        """
        pass
