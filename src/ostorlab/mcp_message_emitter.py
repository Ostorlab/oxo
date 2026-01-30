"""MCP Message Emitter module for emitting messages to RabbitMQ from MCP servers.

This module provides a lightweight interface for MCP (Model Context Protocol) servers
to emit messages to the Ostorlab message bus without requiring full agent functionality.
"""

import asyncio
import logging
import uuid
from typing import Any, Optional, Dict

from ostorlab.agent.message import message as agent_message
from ostorlab.agent.mixins import agent_mq_mixin
from ostorlab.runtimes import definitions as runtime_definitions

logger = logging.getLogger(__name__)

class MCPMessageHandler(agent_mq_mixin.AgentMQMixin):
    """MCP Message Emitter for sending messages from MCP servers to RabbitMQ.

    This class provides a lightweight interface for MCP servers to emit messages
    to the Ostorlab message bus without the full agent functionality. It only
    sends messages and does not listen to or process incoming messages.

    Example:
        ```python
        # Initialize the emitter
        emitter = MCPMessageHandler(
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
        self._control_message: Optional[agent_message.Message] = None
        logger.info("initializing MCP message emitter: %s", name)
        self._emitter_name = name
        self._out_selectors = out_selectors
        self._agent_settings = agent_settings
        self._loop = asyncio.get_event_loop()
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

    @classmethod
    async def create_and_start(
            cls,
            name: str,
            out_selectors: list[str],
            agent_settings: runtime_definitions.AgentSettings,
    ) -> "MCPMessageHandler":
        """Construct the emitter and connect to MQ immediately."""
        emitter = cls(
            name=name,
            out_selectors=out_selectors,
            agent_settings=agent_settings,
        )
        await emitter._start()
        return emitter

    async def _start(self) -> None:
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
        return self.emit_raw(selector, message.raw, message_id=message_id)

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
        if (
                any(
                    selector.startswith(out_selector) for out_selector in self.out_selectors
                )
                is False
        ):
            logger.error("selector not present in list of out selectors")
            # CAUTION: this check is enforced on the client-side only in certain runtimes
            raise ValueError(
                f"{selector} is not in {''.join(self.out_selectors)}"
            )

        logger.debug("call to send message with %s", selector)
        # A random unique UUID is added to ensure messages could be resent. Storage master ensures that a message with
        # the same selector and message body is sent only once to the bus.
        if message_id is None:
            routing_key = f"{selector}.{uuid.uuid4()}"
        else:
            routing_key = f"{selector}.{message_id}"

        control_message = self._prepare_message(raw)
        logger.info("Sending message bytes_len=%d to routing_key=%s", len(control_message), routing_key)

        try:
            running_loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop in this thread => safe to use the mixin's sync wrapper.
            self.mq_send_message(routing_key, control_message)
            logger.debug("done call to send_message")
            return

        if running_loop is self._loop:
            # Fire-and-forget; avoids deadlock while keeping a sync API.
            self._loop.create_task(self.async_mq_send_message(routing_key, control_message))
            return

        # Running loop in this thread => schedule on the emitter loop and wait here (not the loop thread).
        future = asyncio.run_coroutine_threadsafe(
            self.async_mq_send_message(routing_key, control_message),
            self._loop,
        )
        future.result()

        print("done call to send_message, here is the control message %s", control_message)

    def _prepare_message(self, raw: bytes) -> bytes:
        if self._control_message is not None:
            agents = [*self._control_message.data["control"]["agents"], self.name]
        else:
            agents = [self.name]
        control_message = agent_message.Message.from_data(
            "v3.control", {"control": {"agents": agents}, "message": raw}
        )
        return control_message.raw


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
