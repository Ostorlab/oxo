"""OpenTelemetry Mixin.

The mixin overrides the behaviour of the main methods of the agent, mainly emit and process to send traces,
metadata, metrics and exceptions.
"""
import io
import logging
from typing import Any, Dict, Optional
from urllib import parse

from opentelemetry import trace
from opentelemetry.exporter.jaeger import thrift as jaeger
from opentelemetry.sdk import trace as trace_provider
from opentelemetry.sdk.trace import export as sdk_export
from opentelemetry.sdk import resources

from ostorlab.runtimes import definitions as runtime_definitions
from ostorlab.agent import definitions as agent_definitions
from ostorlab.agent import message as agent_message


logger = logging.getLogger(__name__)


class TraceExporter:
    """Class responsible for preparing the respective OpenTelemetry Span Exporter for an input tracing url."""

    def __init__(self, tracing_collector_url: str):
        self._tracing_collector_url = tracing_collector_url
        # specialized fields for the different collectors.
        self._file: Optional[io.IOBase] = None

    def close(self):
        if self._file is not None:
            self._file.close()

    def get_trace_exporter(self) -> sdk_export.SpanExporter:
        """
        Returns a span exporter instance depending on the OpenTelemtry collector url argument.
        The urls are customized to respect the following format:
            name_of_the_tracing_tool:hostname:port
            eg: jaeger:jaeger-host:8631
        """
        parsed_url = parse.urlparse(self._tracing_collector_url)
        scheme = parsed_url.scheme
        if scheme == 'jaeger':
            return self._get_jaeger_exporter(parsed_url)
        elif scheme == 'file':
            return self._get_file_exporter(parsed_url)
        else:
            raise NotImplementedError(f'Invalid tracer type {scheme}')

    def _get_file_exporter(self, parsed_url):
        file_path = parsed_url.path
        self._file = open(file_path, 'w', encoding='utf-8')
        file_exporter = sdk_export.ConsoleSpanExporter(out=self._file)
        logger.info('Configuring file exporter..')
        return file_exporter

    def _get_jaeger_exporter(self, parsed_url):
        netloc = parsed_url.netloc
        hostname, port = netloc.split(':')[0], int(netloc.split(':')[1])
        jaeger_exporter = jaeger.JaegerExporter(
            agent_host_name=hostname,
            agent_port=port,
            udp_split_oversized_batches=True,
        )
        logger.info('Configuring jaeger exporter..')
        return jaeger_exporter


class OpenTelemetryMixin:
    """OpenTelemetryMixin to send telemetry data of the agent behaviour. The mixin enables tracking information
    like when was a message processed or emitted, using which selector,
    how much time it took to serialize or deserialize a message, and report exceptions when they occur..etc.
    """

    def __init__(self, agent_definition: agent_definitions.AgentDefinition,
                 agent_settings: runtime_definitions.AgentSettings) -> None:
        """Initializes the mixin from the agent settings.

        Args:
            agent_settings: Agent runtime settings.
        """
        super().__init__(agent_definition=agent_definition, agent_settings=agent_settings)
        self._agent_settings = agent_settings
        url = agent_settings.tracing_collector_url
        if url is not None:
            self._exporter = TraceExporter(url)
            provider = trace_provider.TracerProvider(
                resource=resources.Resource.create({resources.SERVICE_NAME: agent_settings.key})
            )
            trace.set_tracer_provider(provider)
            self._span_processor = sdk_export.BatchSpanProcessor(self._exporter.get_trace_exporter())
            trace.get_tracer_provider().add_span_processor(self._span_processor)
            self.tracer = trace.get_tracer(__name__)



    def force_flush(self):
        self._span_processor.force_flush()

    def process_message(self, selector: str, message: bytes) -> None:
        """Overridden agent process message method to add OpenTelemetry traces.
        Processes raw message received from BS.

        Args:
            selector: destination selector with full path, including UUID set by default.
            message: raw bytes message.

        Returns:
            None
        """
        if self._agent_settings.tracing_collector_url is not None:
            logger.debug('recording process message trace..')
            with self.tracer.start_as_current_span('process_message') as process_msg_span:
                super().process_message(selector, message)
                process_msg_span.set_attribute('agent.name', self.name)
                process_msg_span.set_attribute('message.selector', selector)
        else:
            super().process_message(selector, message)


    def process(self, message: agent_message.Message) -> None:
        """Overridden agen process method to add OpenTelemetry traces.
        Method responsible for processing a message.

        Args:
            message: message received from with selector and data.

        Returns:
            None
        """
        if self._agent_settings.tracing_collector_url is not None:
            logger.debug('recording process trace..')
            with self.tracer.start_as_current_span('process') as process_span:
                super().process(message)
                process_span.set_attribute('agent.name', self.name)
                process_span.set_attribute('message.selector', message.selector)
        else:
            super().process(message)


    def emit(self, selector: str, data: Dict[str, Any]) -> None:
        """Overriden emit method of the agent to add OpenTelemetry traces.
        Sends a message to all listening agents on the specified selector.

        Args:
            selector: target selector.
            data: message data to be serialized.
        Raises:
            NonListedMessageSelectorError: when selector is not part of listed out selectors.

        Returns:
            None
        """
        if self._agent_settings.tracing_collector_url is not None:
            with self.tracer.start_as_current_span('emit_message') as emit_span:
                logger.debug('recording emit message trace..')
                super().emit(selector, data)
                emit_span.set_attribute('agent.name', self.name)
                emit_span.set_attribute('message.selector', selector)
        else:
            super().emit(selector, data)


    def start(self) -> None:
        """Overriden agent start method to add OpenTelemetry traces.
        The method implements one-off or long-processing non-receiving agents

        Returns:
            None
        """
        if self._agent_settings.tracing_collector_url is not None:
            with self.tracer.start_as_current_span('start_agent') as start_span:
                logger.debug('recording start agent trace..')
                super().start()
                start_span.set_attribute('agent.name', self.name)
        else:
            super().start()


    def process_cleanup(self) -> None:
        """Overriden agent message cleanup to add OpenTelemetry traces
        The method will be called once process is completed or even in the case of a failure.

        Returns:
            None
        """
        if self._agent_settings.tracing_collector_url is not None:
            with self.tracer.start_as_current_span('process_cleanup') as cleanup_span:
                logger.debug('recording agent process cleanup trace..')
                super().process_cleanup()
                cleanup_span.set_attribute('agent.name', self.name)
        else:
            super().process_cleanup()


    def at_exit(self) -> None:
        """Overridable at exit method to perform cleanup in the case of expected and unexpected agent termination.

        Returns:
            None
        """
        if self._agent_settings.tracing_collector_url is not None:
            with self.tracer.start_as_current_span('at_exit') as at_exit_span:
                logger.debug('recording agent at exit trace..')
                self.force_flush()
                self._file.close()
                at_exit_span.set_attribute('agent.name', self.name)
                super().at_exit()
        else:
            super().at_exit()
