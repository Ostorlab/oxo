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
import os
import pathlib
import sys
import threading
import uuid
import json
from typing import Dict, Any, NoReturn

from ostorlab import exceptions
from ostorlab.agent import definitions as agent_definitions
from ostorlab.agent import message as agent_message
from ostorlab.agent.mixins import agent_healthcheck_mixin
from ostorlab.agent.mixins import agent_mq_mixin
from ostorlab.runtimes import definitions as runtime_definitions

AGENT_DEFINITION_PATH = '/tmp/ostorlab.yaml'

logger = logging.getLogger(__name__)


class NonListedMessageSelectorError(exceptions.OstorlabError):
    """Emit selector is not listed in the out_selector list."""


class AgentMixin(agent_mq_mixin.AgentMQMixin, agent_healthcheck_mixin.AgentHealthcheckMixin, abc.ABC):
    """Agent mixin handles all the heavy lifting.

    The agent mixin start the healthcheck service, connects the MQ and start listening to the process message.
    """

    def __init__(self,
                 agent_definition: agent_definitions.AgentDefinition,
                 agent_settings: runtime_definitions.AgentSettings
                 ) -> None:
        """Inits the agent configuration from the Yaml agent definition.

        Args:
            agent_definition: Agent definition dictating the settings of the agent, like name, in_selectors ...
            agent_settings: The running instance definition dictating custom settings of the agent like bus
             URL.
        """
        self._loop = asyncio.get_event_loop()
        self._agent_definition = agent_definition
        self._agent_settings = agent_settings
        self.name = agent_definition.name
        self.in_selectors = agent_definition.in_selectors
        self.out_selectors = agent_definition.out_selectors
        # Arguments are defined in the agent definition, and can have a default value. The value can also be set from
        # the scan definition in the agent group. Therefore, we read both and override the value from the passed args.
        self.defined_args = agent_definition.args
        self.passed_args = agent_settings.args
        self.bus_url = agent_settings.bus_url
        self.bus_exchange_topic = agent_settings.bus_exchange_topic
        self.bus_managment_url = agent_settings.bus_management_url
        self.bus_vhost = agent_settings.bus_vhost
        agent_mq_mixin.AgentMQMixin.__init__(self,
                                             name=agent_definition.name,
                                             # Selectors are mapped to queue binding that listen to all
                                             # sub-routing keys.
                                             keys=[f'{s}.#' for s in self.in_selectors],
                                             url=self.bus_url,
                                             topic=self.bus_exchange_topic)
        agent_healthcheck_mixin.AgentHealthcheckMixin.__init__(self, name=agent_definition.name,
                                                               host=agent_settings.healthcheck_host,
                                                               port=agent_settings.healthcheck_port)

    @property
    def definition(self) -> agent_definitions.AgentDefinition:
        """Agent definition property."""
        return self._agent_definition

    @property
    def settings(self) -> runtime_definitions.AgentSettings:
        """Agent settings property."""
        return self._agent_settings

    @property
    def args(self) -> Dict[str, Any]:
        """Agent arguments as passed from definition and settings."""
        arguments = {}
        # First read the agent default values.
        for a in self.definition.args:
            arguments[a['name']] = a.get('value')
        # Override the default values from settings.
        for a in self.settings.args:
            if a.type == 'binary':
                arguments[a.name] = a.value
            else:
                arguments[a.name] = json.loads(a.value.decode())

        return arguments

    @property
    def universe(self):
        """Returns the current scan universe.

        A universe is the group of agents and services in charge of running a scan. The universe is defined
        by the runtime."""
        return os.environ.get('UNIVERSE')

    def run(self) -> None:
        """Starts running the agent.

        Connects to the agent bus, start health check and start listening to new messages.
        """
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
            self._loop.close()


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
        Raises:
            NonListedMessageSelectorError: when selector is not part of listed out selectors.

        Returns:
            None
        """
        message = agent_message.Message.from_data(selector, data)
        self.emit_raw(selector, message.raw)

    def emit_raw(self, selector: str, raw: bytes) -> None:
        """Sends a message to all listening agents on the specified selector with no serialization.

        Args:
            selector: target selector.
            raw: raw message to send.
        Raises:
            NonListedMessageSelectorError: when selector is not part of listed out selectors.

        Returns:
            None
        """
        if selector not in self.out_selectors:
            logger.error('selector not present in list of out selectors')
            # CAUTION: this check is enforced on the client-side only in certain runtimes
            raise NonListedMessageSelectorError(f'{selector} is not in {"".join(self.out_selectors)}')

        logger.debug('call to send message with %s', selector)
        # A random unique UUID is added to ensure messages could be resent. Storage master ensures that a message with
        # the same selector and message body is sent only once to the bus.
        selector = f'{selector}.{uuid.uuid1()}'
        self.mq_send_message(selector, raw)
        logger.debug('done call to send_message')

    @classmethod
    def main(cls, args=None) -> NoReturn:
        """Prepares the agents class by reading the agent definition and runtime settings.

        By the default, the class main expects the definition file to be at `agent.yaml` and settings to be at
        `/tmp/settings.binproto`.

        The values can be overridden by passing the arguments `--definition` and `--settings`.

        The definition file defines the agents, like name, description, consumed and generated selectors. The definition
        might include information on how to run the agent, but those can be overridden by the scan runtime.

        The settings file defines how the agent is running, what services are enabled and what addresses should it
        connect to. Some of these settings are consumed by the scan runtime, others are consumed by the agent itself.

        Args:
            args: Arguments passed to the argument parser. These are added for testability.

        Returns:
            The function do not return unless an error is detected. The agent instance starts running and never returns.
        """

        # Settings the args to make the code testable without mocking.
        if not args:
            args = sys.argv[1:]

        parser = argparse.ArgumentParser()
        parser.add_argument('-s', '--settings',
                            default='/tmp/settings.binproto',
                            help='Agent binary proto settings.')
        args = parser.parse_args(args)
        logger.info('running agent with definition %s and settings %s', AGENT_DEFINITION_PATH, args.settings)

        if not pathlib.Path(AGENT_DEFINITION_PATH).exists():
            logger.error('definition file does not exist')
            sys.exit(2)
        if not pathlib.Path(args.settings).exists():
            logger.error('settings file does not exist')
            sys.exit(2)

        with open(AGENT_DEFINITION_PATH, 'r', encoding='utf-8') as f_definition,\
                open(args.settings, 'rb') as f_settings:
            agent_definition = agent_definitions.AgentDefinition.from_yaml(f_definition)
            agent_settings = runtime_definitions.AgentSettings.from_proto(f_settings.read())
            instance = cls(agent_definition=agent_definition, agent_settings=agent_settings)
            logger.debug('running agent instance')
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
