"""MCP Message Emitter module for emitting messages to RabbitMQ from MCP servers.

This module provides a lightweight interface for MCP (Model Context Protocol) servers
to emit messages to the Ostorlab message bus without requiring full agent functionality.
"""

import asyncio
import logging
from typing import Any, Optional

from ostorlab.agent.message import message as agent_message
from ostorlab.agent.mixins import agent_mq_mixin
from ostorlab.runtimes import definitions as runtime_definitions

logger = logging.getLogger(__name__)


class MCPMessageEmitter(agent_mq_mixin.AgentMQMixin):
    """MCP Message Emitter for sending messages from MCP servers to RabbitMQ.

    This class provides a lightweight interface for MCP servers to emit messages
    to the Ostorlab message bus without the full agent functionality. It only
    sends messages and does not listen to or process incoming messages.

    Example:
        ```python
        # Initialize the emitter
        emitter = MCPMessageEmitter(
            name="mcp_vulnerability_scanner",
            out_selectors=["v3.report.vulnerability"],
            agent_settings=agent_settings
        )

        # Start the connection
        await emitter.start()

        # Emit a message
        emitter.emit("v3.report.vulnerability", {
            "title": "XSS Vulnerability Found",
            "risk_rating": "HIGH",
            "cvss_v3_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N"
        })

        # Close the connection when done
        await emitter.close()
        ```
    """

    def __init__(
        self,
        name: str,
        out_selectors: list[str],
        agent_settings: runtime_definitions.AgentSettings,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        """Initialize the MCP message emitter.

        Args:
            name: Name of the MCP emitter instance. This will be used to identify
                the source of messages in the system.
            out_selectors: List of message selectors this emitter is allowed to send
                messages to. Messages sent to selectors not in this list will raise
                a ValueError.
            agent_settings: Agent settings containing bus connection information such
                as bus_url and bus_exchange_topic.
            loop: Optional event loop to use. If not provided, the current event loop
                will be used.
        """
        self._emitter_name = name
        self._out_selectors = out_selectors
        self._agent_settings = agent_settings
        self._loop = loop or asyncio.get_event_loop()
        self._started = False

        # Initialize the MQ mixin with no input keys since we only send messages
        agent_mq_mixin.AgentMQMixin.__init__(
            self,
            name=name,
            keys=[],  # MCP emitter doesn't listen, only sends
            url=agent_settings.bus_url,
            topic=agent_settings.bus_exchange_topic,
            loop=self._loop,
        )

    async def start(self) -> None:
        """Initialize the connection to the message queue.

        This method must be called before attempting to emit any messages.
        It sets up the connection pools and prepares the emitter for sending messages.

        Raises:
            ConnectionError: If unable to connect to the message bus.
        """
        logger.info("Starting MCP message emitter: %s", self._emitter_name)
        await self.mq_init()
        self._started = True
        logger.info("MCP message emitter started successfully")

    def emit(
        self, selector: str, data: dict[str, Any], priority: Optional[int] = None
    ) -> None:
        """Send a message to the specified selector.

        Args:
            selector: Target selector for the message. Must match one of the allowed
                out_selectors (or be a sub-selector of an allowed one).
            data: Message data dictionary to serialize and send. This should conform
                to the schema expected by agents listening to the selector.
            priority: Optional message priority (0-255). Higher priority messages
                are processed first by receiving agents.

        Raises:
            ValueError: If selector is not in the allowed out_selectors list or if
                the emitter has not been started yet.
            RuntimeError: If there's an error sending the message to the bus.
        """
        if not self._started:
            raise ValueError(
                "MCP emitter must be started before emitting messages. Call await emitter.start() first."
            )

        # Check if the selector matches any of the allowed out_selectors
        if not any(
            selector.startswith(out_selector) for out_selector in self._out_selectors
        ):
            raise ValueError(
                f"Selector '{selector}' not in allowed out_selectors: {self._out_selectors}"
            )

        try:
            # Create the message using the Ostorlab message format
            message = agent_message.Message.from_data(selector, data)

            # Wrap in a control message to identify the source
            control_message = agent_message.Message.from_data(
                "v3.control",
                {"control": {"agents": [self._emitter_name]}, "message": message.raw},
            )

            # Send the message to the bus
            self.mq_send_message(
                selector, control_message.raw, message_priority=priority
            )
            logger.debug(
                "MCP emitter '%s' sent message to selector: %s",
                self._emitter_name,
                selector,
            )
        except Exception as e:
            logger.error(
                "Error emitting message from MCP emitter '%s' to selector '%s': %s",
                self._emitter_name,
                selector,
                e,
            )
            raise RuntimeError(f"Failed to emit message: {e}") from e

    async def close(self) -> None:
        """Close the message queue connection and cleanup resources.

        This should be called when the MCP emitter is no longer needed to properly
        release connection resources.
        """
        logger.info("Closing MCP message emitter: %s", self._emitter_name)
        self._started = False
        # Close connection pools
        if hasattr(self, "_channel_pool"):
            await self._channel_pool.close()
        if hasattr(self, "_connection_pool"):
            await self._connection_pool.close()
        logger.info("MCP message emitter closed successfully")

    @property
    def name(self) -> str:
        """Get the name of the emitter."""
        return self._emitter_name

    @property
    def out_selectors(self) -> list[str]:
        """Get the list of allowed output selectors."""
        return self._out_selectors

    @property
    def is_started(self) -> bool:
        """Check if the emitter has been started."""
        return self._started

    def process_message(self, selector: str, message: bytes) -> None:
        """Process message callback required by AgentMQMixin.

        Since MCP emitters only send messages and don't receive them, this method
        is not used and raises NotImplementedError if called.

        Args:
            selector: Message selector (unused).
            message: Message body (unused).

        Raises:
            NotImplementedError: Always, as MCP emitters don't process incoming messages.
        """
        raise NotImplementedError(
            "MCP emitters do not process incoming messages. "
            "This method should never be called."
        )
