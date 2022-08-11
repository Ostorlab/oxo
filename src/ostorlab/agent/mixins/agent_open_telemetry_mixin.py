"""OpenTelemetry Mixin.

The mixin overrides the behaviour of the main methods of the agent, mainly emit and process to send traces,
metadata, metrics and exceptions.
"""
import logging
from typing import Any, Dict
from urllib import parse
import pathlib

from opentelemetry import trace
from opentelemetry.exporter.jaeger import thrift as jaeger
from opentelemetry.sdk import trace as trace_provider
from opentelemetry.sdk.trace import export as sdk_export
from opentelemetry.sdk import resources

from ostorlab.runtimes import definitions as runtime_definitions
from ostorlab.agent import definitions as agent_definitions


logger = logging.getLogger(__name__)


class TraceExporter:
    """Class responsible for preparing the respective OpenTelemetry Span Exporter for an input tracing url."""
    @staticmethod
    def get_trace_exporter(tracing_collector_url: str) -> sdk_export.SpanExporter:
        """
        Returns a span exporter instance depending on the OpenTelemtry collector url argument.
        The urls are customized to respect the following format:
            name_of_the_tracing_tool:hostname:port
            eg: jaeger:jaeger-host:8631
        """
        parsed_url = parse.urlparse(tracing_collector_url)
        scheme = parsed_url.scheme
        if scheme.startswith('jaeger'):
            netloc = parsed_url.netloc
            hostname, port = netloc.split(':')[0], int(netloc.split(':')[1])
            jaeger_exporter = jaeger.JaegerExporter(
                agent_host_name=hostname,
                agent_port=port,
                udp_split_oversized_batches=True,
            )
            logger.info('Configuring jaeger exporter..')
            return jaeger_exporter
        elif scheme.startswith('file'):
            file_path = tracing_collector_url.split('file://')[-1]
            file_path = pathlib.Path(file_path)
            spans_output_file = open(file_path, 'w', encoding='utf-8')
            file_exporter = sdk_export.ConsoleSpanExporter(out=spans_output_file)
            logger.info('Configuring file exporter..')
            return file_exporter
        else:
            #redirect to console.
            console_exporter = sdk_export.ConsoleSpanExporter()
            logger.info('Configuring console exporter..')
            return console_exporter




class OpenTelemtryMixin:
    """OpenTelemtryMixin to send telemtry data of the agent behaviour. The mixin enables tracking information
    like when was a message processed or emitted, using which selector,
    how much time it took to serialze or deserialize a message, and report exceptions when they occur..etc.
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
        self._exporter = TraceExporter.get_trace_exporter(url)
        runtime_name = agent_settings.bus_exchange_topic.split('ostorlab_topic_')[-1]
        provider = trace_provider.TracerProvider(
                resource=resources.Resource.create({resources.SERVICE_NAME: f'{agent_settings.key}_{runtime_name}'})
            )
        trace.set_tracer_provider(provider)
        if isinstance(self._exporter, sdk_export.ConsoleSpanExporter) is True:
            span_processor = sdk_export.BatchSpanProcessor(self._exporter, max_export_batch_size=1)
        else:
            span_processor = sdk_export.BatchSpanProcessor(self._exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)
        # provider.add_span_processor(sdk_export.BatchSpanProcessor(self._exporter))
        # trace.set_tracer_provider(provider)
        self.tracer = trace.get_tracer(__name__)


    def process_message(self, selector: str, message: bytes) -> None:
        """Overriden process message method of the agent to add OpenTelemetry traces.
        Processes raw message received from BS.

        Args:
            selector: destination selector with full path, including UUID set by default.
            message: raw bytes message.

        Returns:
            None
        """
        logger.info('IN the trace mixin process %s', self._agent_settings.tracing_collector_url)
        if self._agent_settings.tracing_collector_url is not None:
            logger.debug('recording process message trace..')
            with self.tracer.start_as_current_span('process_message') as process_span:
                super().process_message(selector, message)
                process_span.set_attribute('agent.name ', self.name)
                process_span.set_attribute('message.selector', selector)
        else:
            super().process_message(selector, message)

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
        logger.info('IN the trace mixin emit %s', self._agent_settings.tracing_collector_url)
        if self._agent_settings.tracing_collector_url is not None:
            with self.tracer.start_as_current_span('emit_message') as emit_span:
                super().emit(selector, data)
                emit_span.set_attribute('agent.name ', self.name)
                emit_span.set_attribute('message.selector', selector)
        else:
            super().emit(selector, data)

