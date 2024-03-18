"""Agent class.

All agents should inherit from the agent class to access the different features, like automated message
serialization, message receiving and sending, selector enrollment, agent health check, etc.

To use it, check out documentations at https://oxo.ostorlab.co/docs.
"""

import abc
import argparse
import asyncio
import base64
import json
import logging
import os
import pathlib
import signal
import sys
import threading
import uuid
from typing import Dict, Any, Optional, Type, List

from ostorlab import exceptions
from ostorlab.agent import definitions as agent_definitions
from ostorlab.agent.message import message as agent_message
from ostorlab.agent.mixins import agent_healthcheck_mixin
from ostorlab.agent.mixins import agent_mq_mixin
from ostorlab.agent.mixins import agent_open_telemetry_mixin as open_telemetry_mixin
from ostorlab.runtimes import definitions as runtime_definitions
from ostorlab.utils import system

GCP_LOGGING_CREDENTIAL_ENV = "GCP_LOGGING_CREDENTIAL"

AGENT_DEFINITION_PATH = "/tmp/ostorlab.yaml"

logger = logging.getLogger(__name__)


class NonListedMessageSelectorError(exceptions.OstorlabError):
    """Emit selector is not listed in the out_selector list."""


class MaximumCyclicProcessReachedError(exceptions.OstorlabError):
    """The cyclic process limit is enforced and reach set value."""


class MaximumDepthProcessReachedError(exceptions.OstorlabError):
    """The processing depth limit is enforced and reached the limit."""


def _setup_logging(agent_key: str, universe: str) -> None:
    gcp_logging_credential = os.environ.get(GCP_LOGGING_CREDENTIAL_ENV)
    if gcp_logging_credential is not None:
        try:
            import google.cloud.logging
            from google.oauth2 import service_account

            info = json.loads(
                base64.b64decode(gcp_logging_credential.encode()).decode()
            )
            credentials = service_account.Credentials.from_service_account_info(info)
            client = google.cloud.logging.Client(credentials=credentials)
            client.setup_logging(labels={"agent_key": agent_key, "universe": universe})
        except ImportError:
            logger.error(
                "Could not import Google Cloud Logging, install it with `pip install 'ostorlab[google-cloud-logging]'"
            )


class AgentMixin(
    agent_mq_mixin.AgentMQMixin, agent_healthcheck_mixin.AgentHealthcheckMixin, abc.ABC
):
    """Agent mixin handles all the heavy lifting.

    The agent mixin start the healthcheck service, connects the MQ and start listening to the process message.
    """

    def __init__(
        self,
        agent_definition: agent_definitions.AgentDefinition,
        agent_settings: runtime_definitions.AgentSettings,
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
        self._control_message: Optional[agent_message.Message] = None
        self.name = agent_definition.name
        self.in_selectors = (
            agent_settings.in_selectors
            if len(agent_settings.in_selectors) > 0
            else agent_definition.in_selectors
        )
        self.out_selectors = agent_definition.out_selectors
        self.cyclic_processing_limit = agent_settings.cyclic_processing_limit
        self.depth_processing_limit = agent_settings.depth_processing_limit
        self.accepted_agents = agent_settings.accepted_agents
        # Arguments are defined in the agent definition, and can have a default value. The value can also be set from
        # the scan definition in the agent group. Therefore, we read both and override the value from the passed args.
        self.defined_args = agent_definition.args
        self.passed_args = agent_settings.args
        self.bus_url = agent_settings.bus_url
        self.bus_exchange_topic = agent_settings.bus_exchange_topic
        self.bus_managment_url = agent_settings.bus_management_url
        self.bus_vhost = agent_settings.bus_vhost
        agent_mq_mixin.AgentMQMixin.__init__(
            self,
            name=agent_definition.name,
            # Selectors are mapped to queue binding that listen to all
            # sub-routing keys.
            keys=[f"{s}.#" for s in self.in_selectors],
            url=self.bus_url,
            topic=self.bus_exchange_topic,
        )
        agent_healthcheck_mixin.AgentHealthcheckMixin.__init__(
            self,
            name=agent_definition.name,
            host=agent_settings.healthcheck_host,
            port=agent_settings.healthcheck_port,
        )
        signal.signal(signal.SIGTERM, self._handle_signal)

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
            arguments[a["name"]] = a.get("value")
        # Override the default values from settings.
        for a in self.settings.args:
            # Enforce that only declared arguments are accepted.
            if a.name not in arguments:
                # TODO(OS-5119): Change behavior to fail of the argument is missing from definition.
                logger.warning(
                    "Argument %s is defined in the agent settings but not in the agent definition. "
                    "Please update your definition file or the agent will fail in the future.",
                    a.name,
                )

            if a.type == "binary":
                arguments[a.name] = a.value
            else:
                arguments[a.name] = json.loads(a.value.decode())

        return arguments

    @property
    def universe(self) -> Optional[str]:
        """Returns the current scan universe.

        A universe is the group of agents and services in charge of running a scan. The universe is defined
        by the runtime."""
        return os.environ.get("UNIVERSE")

    def run(self) -> None:
        """Starts running the agent.

        Connects to the agent bus, start health check and start listening to new messages.
        """
        self.add_healthcheck(self.is_healthy)
        self.start_healthcheck()
        self._loop.run_until_complete(self.mq_init())
        logger.debug("calling start method")
        # This is call in a thread to avoid blocking calls from affecting the MQ heartbeat running on the main thread.
        t = threading.Thread(target=self.start)
        t.start()
        t.join()
        logger.debug("calling start method done")
        try:
            if self.in_selectors is not None and len(self.in_selectors) > 0:
                logger.debug("starting mq run")
                self._loop.run_until_complete(self.mq_run())
                self._loop.run_forever()
        finally:
            logger.debug("closing bus and loop")
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

        self._control_message = agent_message.Message.from_raw("v3.control", message)
        raw_message = self._control_message.data["message"]
        # remove the UUID from the selector:
        selector = ".".join(selector.split(".")[:-1])
        object_message = agent_message.Message.from_raw(selector, raw_message)

        # Validate the message before processing it.
        try:
            if self._is_valid_message() is False:
                return None
        except MaximumCyclicProcessReachedError:
            self.on_max_cyclic_process_reached(object_message)
            return None
        except MaximumDepthProcessReachedError:
            self.on_max_depth_process_reached(object_message)
            return None

        try:
            logger.debug("Call to process with message= %s", raw_message)
            self.process(object_message)
        except Exception as e:
            system_info = system.get_system_info()
            if system_info is not None:
                logger.error("System Info: %s", system_info)
            logger.error("Message: %s", object_message)
            logger.exception("Exception: %s", e)
        finally:
            self.process_cleanup()
            logger.debug("done call to process message")
            # Flush all logging handlers to ensure remote logging is sent before app shutdown.
            for h in logger.handlers:
                h.flush()

    def _is_valid_message(self) -> bool:
        """Check the message received is valid, currently only check for cyclic processing limit."""
        control_agents: list[str] = self._control_message.data.get("control", {}).get(
            "agents", []
        )
        if (
            self.cyclic_processing_limit is not None
            and self.cyclic_processing_limit != 0
        ):
            if control_agents.count(self.name) >= self.cyclic_processing_limit:
                raise MaximumCyclicProcessReachedError()

        if self.depth_processing_limit is not None and self.depth_processing_limit != 0:
            if len(control_agents) >= self.depth_processing_limit:
                agent_path = " -> ".join(control_agents)
                error_message = (
                    f"The maximum depth processing limit of {self.depth_processing_limit} agents is reached. "
                    f"Agents path: {agent_path}"
                )
                raise MaximumDepthProcessReachedError(error_message)

        if (
            len(control_agents) > 0
            and self.accepted_agents is not None
            and len(self.accepted_agents) > 0
        ):
            sender_agent = control_agents[-1]
            if sender_agent not in self.accepted_agents:
                return False

        return True

    @abc.abstractmethod
    def process_cleanup(self) -> None:
        """Overridable message cleanup method to be called once process is completed or even in the case of a failure.

        Returns:
            None
        """
        raise NotImplementedError()

    def _handle_signal(self, *args) -> None:
        """Call the Agent `at_exit` method responsible for executing cleanup
        in the case of unexpected agent termination.
        """
        del args
        self.at_exit()
        sys.exit()

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
        raise NotImplementedError("Missing process method implementation.")

    @abc.abstractmethod
    def process(self, message: agent_message.Message) -> None:
        """Overridable message processing method.

        Args:
            message: message received from with selector and data.

        Returns:
            None
        """
        raise NotImplementedError("Missing process method implementation.")

    def emit(
        self, selector: str, data: Dict[str, Any], message_id: Optional[str] = None
    ) -> None:
        """Sends a message to all listening agents on the specified selector.

        Args:
            selector: target selector.
            data: message data to be serialized.
            message_id: An id that will be added to the tail of the message.
        Raises:
            NonListedMessageSelectorError: when selector is not part of listed out selectors.

        Returns:
            None
        """
        message = agent_message.Message.from_data(selector, data)
        self.emit_raw(selector, message.raw, message_id=message_id)

    @abc.abstractmethod
    def on_max_cyclic_process_reached(self, message: agent_message.Message) -> None:
        """Overridable method triggered on max cyclic process reached.

        Returns:
            None
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def on_max_depth_process_reached(self, message: agent_message.Message) -> None:
        """Overridable method triggered on max processing depth reached."""
        raise NotImplementedError()

    def emit_raw(
        self, selector: str, raw: bytes, message_id: Optional[str] = None
    ) -> None:
        """Sends a message to all listening agents on the specified selector with no serialization.

        Args:
            selector: target selector.
            raw: raw message to send.
            message_id: An id that will be added to the tail of the message.
        Raises:
            NonListedMessageSelectorError: when selector is not part of listed out selectors.

        Returns:
            None
        """
        if selector not in self.out_selectors:
            logger.error("selector not present in list of out selectors")
            # CAUTION: this check is enforced on the client-side only in certain runtimes
            raise NonListedMessageSelectorError(
                f'{selector} is not in {"".join(self.out_selectors)}'
            )

        logger.debug("call to send message with %s", selector)
        # A random unique UUID is added to ensure messages could be resent. Storage master ensures that a message with
        # the same selector and message body is sent only once to the bus.
        if message_id is None:
            selector = f"{selector}.{uuid.uuid4()}"
        else:
            selector = f"{selector}.{message_id}"

        control_message = self._prepare_message(raw)
        self.mq_send_message(selector, control_message)
        logger.debug("done call to send_message")

    def _prepare_message(self, raw: bytes) -> bytes:
        if self._control_message is not None:
            agents = [*self._control_message.data["control"]["agents"], self.name]
        else:
            agents = [self.name]
        control_message = agent_message.Message.from_data(
            "v3.control", {"control": {"agents": agents}, "message": raw}
        )
        return control_message.raw

    @classmethod
    def main(cls: Type["AgentMixin"], args: Optional[List[str]] = None) -> None:
        """Prepares the agents class by reading the agent definition and runtime settings.

        By the default, the class main expects the definition file to be at `agent.yaml` and settings to be at
        `/tmp/settings.binproto`.

        The values can be overridden by passing the arguments `--definition` and `--settings`.

        The definition file defines the agents, like name, description, consumed and generated selectors. The definition
        might include information on how to run the agent, but those can be overridden by the scan runtime.

        The settings file defines how the agent is running, what services are enabled and what addresses should it
        connect to. Some of these settings are consumed by the scan runtime, others are consumed by the agent itself.

        Remote Logging:
            If "GCP_LOGGING_CREDENTIAL" is present in the env variables, the Agent will use it to enable
            remote logging to a GCP project.

        Args:
            args: Arguments passed to the argument parser. These are added for testability.

        Returns:
            The function do not return unless an error is detected. The agent instance starts running and never returns.
        """

        # Settings the args to make the code testable without mocking.
        if not args:
            args = sys.argv[1:]

        parser = argparse.ArgumentParser()
        parser.add_argument(
            "-s",
            "--settings",
            default="/tmp/settings.binproto",
            help="Agent binary proto settings.",
        )
        parsed_args = parser.parse_args(args)
        logger.info(
            "running agent with definition %s and settings %s",
            AGENT_DEFINITION_PATH,
            parsed_args.settings,
        )

        if not pathlib.Path(AGENT_DEFINITION_PATH).exists():
            logger.error("definition file does not exist")
            sys.exit(2)
        if not pathlib.Path(parsed_args.settings).exists():
            logger.error("settings file does not exist")
            sys.exit(2)

        with open(AGENT_DEFINITION_PATH, "r", encoding="utf-8") as f_definition, open(
            parsed_args.settings, "rb"
        ) as f_settings:
            agent_definition = agent_definitions.AgentDefinition.from_yaml(f_definition)
            agent_settings = runtime_definitions.AgentSettings.from_proto(
                f_settings.read()
            )

            _setup_logging(
                agent_key=agent_settings.key, universe=os.environ.get("UNIVERSE")
            )

            instance = cls(
                agent_definition=agent_definition, agent_settings=agent_settings
            )
            logger.debug("running agent instance")
            instance.run()


class Agent(open_telemetry_mixin.OpenTelemetryMixin, AgentMixin):
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

    For example and more details on how to implement an agent, refer to https://oxo.ostorlab.co/tutorials/write_an_agent.
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
        raise NotImplementedError("Missing process method implementation.")

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

    def on_max_cyclic_process_reached(self, message: agent_message.Message) -> None:
        """Overridable method triggered on max cyclic process reached.

        Returns:
            None
        """
        pass

    def on_max_depth_process_reached(self, message: agent_message.Message) -> None:
        """Overridable method triggered on max processing depth reached."""
        pass
