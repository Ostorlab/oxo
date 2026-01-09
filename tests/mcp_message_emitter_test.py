"""Unit tests for MCP Message Emitter."""

from unittest import mock

import pytest

from ostorlab import mcp_message_emitter
from ostorlab.runtimes import definitions as runtime_definitions


@pytest.fixture
def agent_settings():
    """Create mock agent settings for testing."""
    return runtime_definitions.AgentSettings(
        key="test_agent",
        bus_url="amqp://guest:guest@localhost:5672//",
        bus_exchange_topic="test_topic",
        args=[],
        healthcheck_port=5000,
        redis_url="redis://localhost:6379",
    )


@pytest.mark.asyncio
async def test_mcp_emitter_initialization(agent_settings):
    """Test MCP emitter initialization."""
    emitter = mcp_message_emitter.MCPMessageEmitter(
        name="test_emitter",
        out_selectors=["v3.report.vulnerability"],
        agent_settings=agent_settings,
    )

    assert emitter.name == "test_emitter"
    assert emitter.out_selectors == ["v3.report.vulnerability"]
    assert emitter.is_started is False


@pytest.mark.asyncio
async def test_mcp_emitter_start(agent_settings):
    """Test MCP emitter start method."""
    emitter = mcp_message_emitter.MCPMessageEmitter(
        name="test_emitter",
        out_selectors=["v3.report.vulnerability"],
        agent_settings=agent_settings,
    )

    with mock.patch.object(emitter, "mq_init", return_value=None):
        await emitter.start()
        assert emitter.is_started is True


@pytest.mark.asyncio
async def test_mcp_emitter_emit_without_start(agent_settings):
    """Test that emitting without starting raises an error."""
    emitter = mcp_message_emitter.MCPMessageEmitter(
        name="test_emitter",
        out_selectors=["v3.report.vulnerability"],
        agent_settings=agent_settings,
    )

    with pytest.raises(ValueError, match="must be started before emitting"):
        emitter.emit("v3.report.vulnerability", {"title": "Test"})


@pytest.mark.asyncio
async def test_mcp_emitter_emit_invalid_selector(agent_settings):
    """Test that emitting to invalid selector raises an error."""
    emitter = mcp_message_emitter.MCPMessageEmitter(
        name="test_emitter",
        out_selectors=["v3.report.vulnerability"],
        agent_settings=agent_settings,
    )

    with mock.patch.object(emitter, "mq_init", return_value=None):
        await emitter.start()

    with pytest.raises(ValueError, match="not in allowed out_selectors"):
        emitter.emit("v3.report.invalid", {"title": "Test"})


@pytest.mark.asyncio
async def test_mcp_emitter_emit_success(agent_settings):
    """Test successful message emission."""
    emitter = mcp_message_emitter.MCPMessageEmitter(
        name="test_emitter",
        out_selectors=["v3.report.vulnerability"],
        agent_settings=agent_settings,
    )

    with mock.patch.object(emitter, "mq_init", return_value=None):
        await emitter.start()

    with mock.patch.object(emitter, "mq_send_message") as mock_send:
        emitter.emit(
            "v3.report.vulnerability",
            {"title": "XSS Vulnerability", "risk_rating": "HIGH"},
        )
        assert mock_send.called
        assert mock_send.call_count == 1


@pytest.mark.asyncio
async def test_mcp_emitter_emit_with_priority(agent_settings):
    """Test message emission with priority."""
    emitter = mcp_message_emitter.MCPMessageEmitter(
        name="test_emitter",
        out_selectors=["v3.report.vulnerability"],
        agent_settings=agent_settings,
    )

    with mock.patch.object(emitter, "mq_init", return_value=None):
        await emitter.start()

    with mock.patch.object(emitter, "mq_send_message") as mock_send:
        emitter.emit(
            "v3.report.vulnerability",
            {"title": "Critical Vulnerability", "risk_rating": "CRITICAL"},
            priority=10,
        )
        assert mock_send.called
        # Check that priority was passed
        call_kwargs = mock_send.call_args
        assert call_kwargs[1]["message_priority"] == 10


@pytest.mark.asyncio
async def test_mcp_emitter_emit_with_subselector(agent_settings):
    """Test that emitting to a subselector of an allowed selector works."""
    emitter = mcp_message_emitter.MCPMessageEmitter(
        name="test_emitter",
        out_selectors=["v3.report"],
        agent_settings=agent_settings,
    )

    with mock.patch.object(emitter, "mq_init", return_value=None):
        await emitter.start()

    with mock.patch.object(emitter, "mq_send_message"):
        # Should work because v3.report.vulnerability starts with v3.report
        emitter.emit("v3.report.vulnerability", {"title": "Test"})


@pytest.mark.asyncio
async def test_mcp_emitter_close(agent_settings):
    """Test MCP emitter close method."""
    emitter = mcp_message_emitter.MCPMessageEmitter(
        name="test_emitter",
        out_selectors=["v3.report.vulnerability"],
        agent_settings=agent_settings,
    )

    with mock.patch.object(emitter, "mq_init", return_value=None):
        await emitter.start()

    # Mock the connection pools
    emitter._channel_pool = mock.AsyncMock()
    emitter._connection_pool = mock.AsyncMock()

    await emitter.close()
    assert emitter.is_started is False
    assert emitter._channel_pool.close.called
    assert emitter._connection_pool.close.called


@pytest.mark.asyncio
async def test_mcp_emitter_process_message_not_implemented(agent_settings):
    """Test that process_message raises NotImplementedError."""
    emitter = mcp_message_emitter.MCPMessageEmitter(
        name="test_emitter",
        out_selectors=["v3.report.vulnerability"],
        agent_settings=agent_settings,
    )

    with pytest.raises(NotImplementedError, match="do not process incoming messages"):
        emitter.process_message("v3.report.vulnerability", b"test")


@pytest.mark.asyncio
async def test_mcp_emitter_multiple_out_selectors(agent_settings):
    """Test MCP emitter with multiple output selectors."""
    emitter = mcp_message_emitter.MCPMessageEmitter(
        name="test_emitter",
        out_selectors=[
            "v3.report.vulnerability",
            "v3.asset.ip.v4",
            "v3.asset.domain_name",
        ],
        agent_settings=agent_settings,
    )

    with mock.patch.object(emitter, "mq_init", return_value=None):
        await emitter.start()

    with mock.patch.object(emitter, "mq_send_message"):
        # All these should work
        emitter.emit("v3.report.vulnerability", {"title": "Test 1"})
        emitter.emit("v3.asset.ip.v4", {"host": "192.168.1.1"})
        emitter.emit("v3.asset.domain_name", {"name": "example.com"})

    # This should fail
    with pytest.raises(ValueError, match="not in allowed out_selectors"):
        emitter.emit("v3.report.secret", {"secret": "password"})
