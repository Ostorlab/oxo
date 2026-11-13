"""Agent class unit tests."""

from __future__ import annotations

import asyncio
import base64
import collections.abc
import datetime
import io
import json
import logging
import multiprocessing as mp
import os
import pathlib
import signal
import sys
import time
import typing
import uuid
from multiprocessing import synchronize
from unittest import mock

import aio_pika
import docker
import pytest
import pytest_asyncio
from aiormq import abc as aiormq_abc
from docker.models import services as docker_services
from pamqp import commands
from pamqp import header
from pytest_mock import plugin

from ostorlab.agent import agent
from ostorlab.agent import definitions as agent_definitions
from ostorlab.agent.message import message as agent_message
from ostorlab.runtimes import definitions as runtime_definitions
from ostorlab.runtimes.local.services import mq
from ostorlab.runtimes.local.services import redis as local_redis_service
from ostorlab.testing import agent as agent_testing
from ostorlab.utils import definitions as utils_definitions
from ostorlab.utils import system

logger = logging.getLogger(__name__)


def _run_agent_until_signal(
    agent_definition: agent_definitions.AgentDefinition,
    agent_settings_proto: bytes,
    message: agent_message.Message,
    mp_event: synchronize.Event,
) -> None:
    """Run the test agent in a separate process until it is terminated."""

    agent_settings = runtime_definitions.AgentSettings.from_proto(agent_settings_proto)

    class TestAgent(agent.Agent):
        """Helper class to test Agent at exit implementation."""

        def __init__(
            self,
            agent_definition: agent_definitions.AgentDefinition,
            agent_settings: runtime_definitions.AgentSettings,
            mp_event: synchronize.Event,
        ) -> None:
            super().__init__(agent_definition, agent_settings)
            self.mp_event = mp_event

        def process(self, message: agent_message.Message) -> None:
            del message
            time.sleep(2000)

        def at_exit(self) -> None:
            self.mp_event.set()

    test_agent = TestAgent(
        agent_definition=agent_definition,
        agent_settings=agent_settings,
        mp_event=mp_event,
    )
    test_agent.process(message)


@pytest.mark.timeout(60)
@pytest.mark.docker
def testAgent_whenAnAgentSendAMessageFromStartAgent_listeningToMessageReceivesIt(
    mq_service: mq.LocalRabbitMQ, redis_service: local_redis_service.LocalRedis
) -> None:
    """The setup of this test seems complicated, but it is the most robust implementation iteration.

    The test also tests for many things at the same time, like start and process lifecycle, message emit and message
    serialization.

    The test defines two agent, a start-only agent that sends a ping and a process-only agent the listens for pings.
    The process agent is start first as a dedicated process to start listening. Once a message is received, a
    multiprocess event is set to True.

    After 1 seconds, all processes are terminated and the event is checked.
    """
    mp_event = mp.Event()

    class StartTestAgent(agent.Agent):
        def start(self) -> None:
            self.emit(
                "v3.healthcheck.ping",
                {"body": f"from test agent at {datetime.datetime.now(datetime.UTC)}"},
            )

    class ProcessTestAgent(agent.Agent):
        def process(self, message: agent_message.Message) -> None:
            logger.info("process is called, setting event")
            mp_event.set()

    start_agent = StartTestAgent(
        agent_definitions.AgentDefinition(
            name="start_test_agent", out_selectors=["v3.healthcheck.ping"]
        ),
        runtime_definitions.AgentSettings(
            key="agent/ostorlab/start_test_agent",
            bus_url="amqp://guest:guest@localhost:5672/",
            bus_exchange_topic="ostorlab_test",
            healthcheck_port=5301,
        ),
    )
    process_agent = ProcessTestAgent(
        agent_definitions.AgentDefinition(
            name="process_test_agent", in_selectors=["v3.healthcheck.ping"]
        ),
        runtime_definitions.AgentSettings(
            key="agent/ostorlab/process_test_agent",
            bus_url="amqp://guest:guest@localhost:5672/",
            bus_exchange_topic="ostorlab_test",
            healthcheck_port=5302,
        ),
    )

    mp_event.clear()
    process_agent_t = mp.Process(target=process_agent.run)
    process_agent_t.start()
    time.sleep(1)
    start_agent_t = mp.Process(target=start_agent.run)
    start_agent_t.start()
    time.sleep(1)
    process_agent_t.terminate()
    start_agent_t.terminate()

    assert mp_event.is_set() is True


def testAgentMain_whenPassedArgsAreValid_runsAgent(
    mocker: plugin.MockerFixture,
) -> None:
    """Test agent main with proper arguments, agent runs."""

    class SampleAgent(agent.Agent):
        """Sample agent"""

    init_mock = mocker.patch("ostorlab.agent.agent.Agent.__init__", return_value=None)
    run_mock = mocker.patch("ostorlab.agent.agent.Agent.run", return_value=None)
    mocker.patch.object(
        agent,
        "AGENT_DEFINITION_PATH",
        str(pathlib.Path(__file__).parent / "dummyagent.yaml"),
    )

    SampleAgent.main(
        ["--settings", str(pathlib.Path(__file__).parent / "settings.binproto")]
    )

    run_mock.assert_called()
    init_mock.assert_called()


def testAgentMain_withNonExistingFile_exits(mocker: plugin.MockerFixture) -> None:
    """Test agent when missing definition or settings files to ensure the command exits."""

    class SampleAgent(agent.Agent):
        """Sample agent"""

    init_mock = mocker.patch("ostorlab.agent.agent.Agent.__init__", return_value=None)
    run_mock = mocker.patch("ostorlab.agent.agent.Agent.run", return_value=None)
    with pytest.raises(SystemExit) as wrapper_exception:
        SampleAgent.main(["--definition", "random", "--settings", "random"])

        run_mock.assert_not_called()
        init_mock.assert_not_called()
        assert isinstance(wrapper_exception.type, SystemExit) is True
        assert wrapper_exception.value.code == 42


def testAgent_withDefaultAndSettingsArgs_returnsExpectedArgs(
    agent_mock: list[agent_message.Message],
) -> None:
    class TestAgent(agent.Agent):
        """Test Agent"""

    test_agent = TestAgent(
        agent_definitions.AgentDefinition(
            name="start_test_agent",
            out_selectors=["v3.healthcheck.ping"],
            args=[
                {"name": "color", "type": "string", "value": None},
                {"name": "speed", "type": "string", "value": b"fast"},
            ],
        ),
        runtime_definitions.AgentSettings(
            key="agent/ostorlab/start_test_agent",
            bus_url="amqp://guest:guest@localhost:5672/",
            bus_exchange_topic="ostorlab_test",
            healthcheck_port=5301,
            args=[
                utils_definitions.Arg(name="speed", type="binary", value=b"slow"),
                utils_definitions.Arg(
                    name="color", type="string", value=json.dumps("red").encode()
                ),
            ],
        ),
    )

    assert test_agent.args == {"color": "red", "speed": b"slow"}


def testAgent_whenMaxPriorityProvided_raisesTypeError(
    mocker: plugin.MockerFixture,
) -> None:
    """Test agent init rejects unsupported explicit queue priority override."""

    mq_init = mocker.patch("ostorlab.agent.mixins.agent_mq_mixin.AgentMQMixin.__init__")
    mocker.patch(
        "ostorlab.agent.mixins.agent_healthcheck_mixin.AgentHealthcheckMixin.__init__",
        return_value=None,
    )
    mocker.patch("ostorlab.agent.agent.signal.signal", return_value=None)

    class TestAgent(agent.Agent):
        """Test Agent"""

    agent_definition = agent_definitions.AgentDefinition(
        name="priority_test_agent",
        in_selectors=["v3.healthcheck.ping"],
    )
    agent_settings = runtime_definitions.AgentSettings(
        key="agent/ostorlab/priority_test_agent",
        bus_url="amqp://guest:guest@localhost:5672/",
        bus_exchange_topic="ostorlab_test",
        healthcheck_port=5301,
    )

    with pytest.raises(TypeError):
        typing.cast(collections.abc.Callable[..., agent.Agent], TestAgent)(
            agent_definition, agent_settings, max_priority=4
        )

    mq_init.assert_not_called()


def testAgent_whenMaxPriorityNotProvided_defaultsToMqPriorityQueue(
    mocker: plugin.MockerFixture,
) -> None:
    """Test agent init always configures the MQ mixin with the hardcoded priority queue."""

    mq_init = mocker.patch("ostorlab.agent.mixins.agent_mq_mixin.AgentMQMixin.__init__")
    mocker.patch(
        "ostorlab.agent.mixins.agent_healthcheck_mixin.AgentHealthcheckMixin.__init__",
        return_value=None,
    )
    mocker.patch("ostorlab.agent.agent.signal.signal", return_value=None)

    class TestAgent(agent.Agent):
        """Test Agent"""

    agent_definition = agent_definitions.AgentDefinition(
        name="priority_test_agent",
        in_selectors=["v3.healthcheck.ping"],
    )
    agent_settings = runtime_definitions.AgentSettings(
        key="agent/ostorlab/priority_test_agent",
        bus_url="amqp://guest:guest@localhost:5672/",
        bus_exchange_topic="ostorlab_test",
        healthcheck_port=5301,
    )

    TestAgent(agent_definition, agent_settings)

    mq_init.assert_called_once_with(
        mocker.ANY,
        name="priority_test_agent",
        keys=["v3.healthcheck.ping.#"],
        url="amqp://guest:guest@localhost:5672/",
        topic="ostorlab_test",
    )


@pytest.mark.xfail(reason="OS-5119: Awaiting deprecation.")
def testAgent_withArgMissingFromDefinition_raisesException(
    agent_mock: list[agent_message.Message],
) -> None:
    class TestAgent(agent.Agent):
        """Test Agent"""

    test_agent = TestAgent(
        agent_definitions.AgentDefinition(
            name="start_test_agent",
            out_selectors=["v3.healthcheck.ping"],
            args=[
                {"name": "color", "type": "string", "value": None},
                {"name": "speed", "type": "string", "value": b"fast"},
            ],
        ),
        runtime_definitions.AgentSettings(
            key="agent/ostorlab/start_test_agent",
            bus_url="amqp://guest:guest@localhost:5672/",
            bus_exchange_topic="ostorlab_test",
            healthcheck_port=5301,
            args=[
                utils_definitions.Arg(name="speed", type="binary", value=b"slow"),
                utils_definitions.Arg(
                    name="color", type="string", value=json.dumps("red").encode()
                ),
                utils_definitions.Arg(
                    name="force", type="string", value=json.dumps("strong").encode()
                ),
            ],
        ),
    )

    assert test_agent.args == {"color": "red", "speed": b"slow"}


def testEmit_whenEmitFromNoProcess_willSendTheAgentNameInControlAgents(
    agent_run_mock: agent_testing.AgentRunInstance,
) -> None:
    """Test emit is adding the agent in the control message."""

    class TestAgent(agent.Agent):
        """Helper class to test OpenTelemetry mixin implementation."""

        def process(self, message: agent_message.Message) -> None:
            pass

    agent_definition = agent_definitions.AgentDefinition(
        name="some_name", out_selectors=["v3.report.vulnerability"]
    )
    agent_settings = runtime_definitions.AgentSettings(
        key="some_key",
    )
    test_agent = TestAgent(
        agent_definition=agent_definition, agent_settings=agent_settings
    )

    technical_detail = """Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum
    has been the standard dummy text ever since the 1500s, when an unknown printer took a galley of type and
    scrambled it to make a type specimen book. when an unknown printer took a galley of type and scrambled it to
    make a type specimen book. """
    test_agent.emit(
        "v3.report.vulnerability",
        {
            "title": "some_title",
            "technical_detail": technical_detail,
            "risk_rating": "MEDIUM",
        },
    )

    assert len(agent_run_mock.control_messages) > 0
    assert agent_run_mock.control_messages[0].data["control"]["agents"] == ["some_name"]


def testProcessMessage_whenCyclicMaxIsSet_callbackCalled(
    agent_run_mock: agent_testing.AgentRunInstance, mocker: plugin.MockerFixture
) -> None:
    """When cyclic limit is set, the process should trigger a callback."""

    process_mock = mocker.Mock()

    class TestAgent(agent.Agent):
        """Helper class to test OpenTelemetry mixin implementation."""

        def process(self, message: agent_message.Message) -> None:
            pass

        def on_max_cyclic_process_reached(self, message: agent_message.Message) -> None:
            process_mock(message)

    agent_definition = agent_definitions.AgentDefinition(
        name="agentX",
        out_selectors=["v3.report.vulnerability"],
    )
    agent_settings = runtime_definitions.AgentSettings(
        key="some_key",
        cyclic_processing_limit=2,
    )
    test_agent = TestAgent(
        agent_definition=agent_definition, agent_settings=agent_settings
    )
    actual_message = agent_message.Message.from_data(
        "v3.healthcheck.ping",
        {
            "body": "Hello, can you hear me?",
        },
    )
    control_message = agent_message.Message.from_data(
        "v3.control",
        {
            "control": {"agents": ["agentY", "agentX", "agentX", "agentX"]},
            "message": actual_message.raw,
        },
    )

    test_agent.process_message(
        f"v3.healthcheck.ping.{uuid.uuid4()}", control_message.raw
    )

    assert process_mock.called is True


def testProcessMessage_whenCyclicMaxIsSetFromDefaultProtoValue_callbackNotCalled(
    agent_run_mock: agent_testing.AgentRunInstance, mocker: plugin.MockerFixture
) -> None:
    """When cyclic limit is not set, the proto default value is 0, the agent behavior must not trigger a callback."""

    process_mock = mocker.Mock()

    class TestAgent(agent.Agent):
        """Helper class to test OpenTelemetry mixin implementation."""

        def process(self, message: agent_message.Message) -> None:
            pass

        def on_max_cyclic_process_reached(self, message: agent_message.Message) -> None:
            process_mock(message)

    agent_definition = agent_definitions.AgentDefinition(
        name="agentX",
        out_selectors=["v3.report.vulnerability"],
    )
    agent_settings = runtime_definitions.AgentSettings.from_proto(
        runtime_definitions.AgentSettings(
            key="some_key",
        ).to_raw_proto()
    )
    test_agent = TestAgent(
        agent_definition=agent_definition, agent_settings=agent_settings
    )

    technical_detail = """Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum
        has been the standard dummy text ever since the 1500s, when an unknown printer took a galley of type and
        scrambled it to make a type specimen book. when an unknown printer took a galley of type and scrambled it to
        make a type specimen book. """
    vuln_message = agent_message.Message.from_data(
        "v3.report.vulnerability",
        {
            "title": "some_title",
            "technical_detail": technical_detail,
            "risk_rating": "MEDIUM",
        },
    )

    message = agent_message.Message.from_data(
        "v3.control",
        {
            "control": {"agents": ["agentY", "agentX", "agentX", "agentX"]},
            "message": vuln_message.raw,
        },
    )

    test_agent.process_message(f"v3.report.vulnerability.{uuid.uuid4()}", message.raw)

    assert process_mock.called is False


def testProcessMessage_whenExceptionRaised_shouldLogErrorWithMessageAndSystemLoad(
    agent_run_mock: agent_testing.AgentRunInstance,
    mocker: plugin.MockerFixture,
) -> None:
    """When an exception is raised, the agent should log the exception, the message that was processed,
    and details about the current state of the system such as cpu, ram..."""

    logger_error = mocker.patch("logging.Logger.error")

    class TestAgent(agent.Agent):
        """Helper class to test OpenTelemetry mixin implementation."""

        def process(self, message: agent_message.Message) -> None:
            raise ValueError("some error")

    agent_definition = agent_definitions.AgentDefinition(
        name="agentX",
        out_selectors=["v3.report.vulnerability"],
    )
    agent_settings = runtime_definitions.AgentSettings.from_proto(
        runtime_definitions.AgentSettings(
            key="some_key",
        ).to_raw_proto()
    )
    test_agent = TestAgent(
        agent_definition=agent_definition, agent_settings=agent_settings
    )
    actual_message = agent_message.Message.from_data(
        "v3.healthcheck.ping",
        {
            "body": "Hello, can you hear me?",
        },
    )
    control_message = agent_message.Message.from_data(
        "v3.control",
        {
            "control": {"agents": ["agentY", "agentX", "agentX", "agentX"]},
            "message": actual_message.raw,
        },
    )

    with pytest.raises(ValueError, match="some error"):
        test_agent.process_message(
            f"v3.healthcheck.ping.{uuid.uuid4()}", control_message.raw
        )

    assert logger_error.call_count == 3
    assert "System Info: %s" in logger_error.call_args_list[0][0][0]
    assert (
        isinstance(logger_error.call_args_list[0][0][1], system.SystemLoadInfo) is True
    )
    assert (
        logger_error.call_args_list[1][0][0]
        == "Error processing message on selector %s"
    )
    assert logger_error.call_args_list[1][0][1] == "v3.healthcheck.ping"
    assert logger_error.call_args_list[1].kwargs["exc_info"] is True
    assert "Message of selector %s: %s" in logger_error.call_args_list[2][0][0]
    assert logger_error.call_args_list[2][0][1] == "v3.healthcheck.ping"
    assert "Hello, can you hear me?" in logger_error.call_args_list[2][0][2]


def testProcessMessage_whenExceptionRaisedAndPsutilNotAvailable_shouldLogErrorWithMessageAndNoSystemLoad(
    agent_run_mock: agent_testing.AgentRunInstance,
    mocker: plugin.MockerFixture,
) -> None:
    """When trying to get system load information and psutil is not available, the agent should log the exception,"""

    logger_error = mocker.patch("logging.Logger.error")
    mocker.patch("psutil.virtual_memory", side_effect=ImportError())

    class TestAgent(agent.Agent):
        """Helper class to test OpenTelemetry mixin implementation."""

        def process(self, message: agent_message.Message) -> None:
            raise ValueError("some error")

    agent_definition = agent_definitions.AgentDefinition(
        name="agentX",
        out_selectors=["v3.report.vulnerability"],
    )
    agent_settings = runtime_definitions.AgentSettings.from_proto(
        runtime_definitions.AgentSettings(
            key="some_key",
        ).to_raw_proto()
    )
    test_agent = TestAgent(
        agent_definition=agent_definition, agent_settings=agent_settings
    )
    actual_message = agent_message.Message.from_data(
        "v3.healthcheck.ping",
        {
            "body": "Hello, can you hear me?",
        },
    )
    control_message = agent_message.Message.from_data(
        "v3.control",
        {
            "control": {"agents": ["agentY", "agentX", "agentX", "agentX"]},
            "message": actual_message.raw,
        },
    )

    with pytest.raises(ValueError, match="some error"):
        test_agent.process_message(
            f"v3.healthcheck.ping.{uuid.uuid4()}", control_message.raw
        )

    assert logger_error.call_count == 2
    assert (
        logger_error.call_args_list[0][0][0]
        == "Error processing message on selector %s"
    )
    assert logger_error.call_args_list[0][0][1] == "v3.healthcheck.ping"
    assert logger_error.call_args_list[0].kwargs["exc_info"] is True
    assert "Message of selector %s: %s" in logger_error.call_args_list[1][0][0]
    assert logger_error.call_args_list[1][0][1] == "v3.healthcheck.ping"
    assert "Hello, can you hear me?" in logger_error.call_args_list[1][0][2]


@pytest.mark.skipif(sys.platform == "win32", reason="Does not run on windows")
def testAgentAtExist_whenTerminationSignalIsSent_shouldInterceptSignalExecuteAtExistAndExit(
    agent_run_mock: agent_testing.AgentRunInstance,
    mocker: plugin.MockerFixture,
    ping_message: agent_message.Message,
) -> None:
    """Ensuring the execution of the `at_exit` method in the case of unexpected agent termination."""
    mp_event = mp.Event()

    class TestAgent(agent.Agent):
        """Helper class to test Agent at exit implementation."""

        def __init__(
            self,
            agent_definition: agent_definitions.AgentDefinition,
            agent_settings: runtime_definitions.AgentSettings,
            mp_event: synchronize.Event,
        ) -> None:
            super().__init__(agent_definition, agent_settings)
            self.mp_event = mp_event

        def process(self, message: agent_message.Message) -> None:
            del message
            time.sleep(2000)

        def at_exit(self) -> None:
            self.mp_event.set()

    agent_definition = agent_definitions.AgentDefinition(
        name="agentX",
        out_selectors=["v3.report.vulnerability"],
    )
    agent_settings = runtime_definitions.AgentSettings.from_proto(
        runtime_definitions.AgentSettings(
            key="testing_agent",
        ).to_raw_proto()
    )

    agent_process = mp.Process(
        target=_run_agent_until_signal,
        args=(
            agent_definition,
            agent_settings.to_raw_proto(),
            ping_message,
            mp_event,
        ),
        daemon=False,
    )
    mp_event.clear()
    agent_process.start()
    time.sleep(3)
    assert agent_process.pid is not None
    os.kill(agent_process.pid, signal.SIGTERM)
    agent_process.join()

    assert mp_event.is_set() is True


def testProcessMessage_whenProcessingDepthLimitIsReached_callbackCalled(
    agent_run_mock: agent_testing.AgentRunInstance, mocker: plugin.MockerFixture
) -> None:
    """When processing depth limit is set and the limit is reached, the process should trigger a callback."""

    on_max_depth_process_reached_mock = mocker.Mock()

    class TestAgent(agent.Agent):
        """Helper class to test the max processing depth limit implementation."""

        def process(self, message: agent_message.Message) -> None:
            pass

        def on_max_depth_process_reached(self, message: agent_message.Message) -> None:
            on_max_depth_process_reached_mock(message)

    agent_definition = agent_definitions.AgentDefinition(
        name="agentX",
        out_selectors=["v3.report.vulnerability"],
    )
    agent_settings = runtime_definitions.AgentSettings(
        key="some_key",
        depth_processing_limit=3,
    )
    test_agent = TestAgent(
        agent_definition=agent_definition, agent_settings=agent_settings
    )
    actual_message = agent_message.Message.from_data(
        "v3.healthcheck.ping",
        {
            "body": "Hello, can you hear me?",
        },
    )
    control_message = agent_message.Message.from_data(
        "v3.control",
        {
            "control": {"agents": ["agent1", "agent2", "agent3", "agent4"]},
            "message": actual_message.raw,
        },
    )

    test_agent.process_message(
        f"v3.healthcheck.ping.{uuid.uuid4()}", control_message.raw
    )

    assert on_max_depth_process_reached_mock.called is True


def testProcessMessage_whenProcessingDepthLimitIsSetAndLimitNotReached_callbackNotCalled(
    agent_run_mock: agent_testing.AgentRunInstance, mocker: plugin.MockerFixture
) -> None:
    """When processing depth limit is set, the process should not trigger a callback if limit is not reached."""

    on_max_depth_process_reached_mock = mocker.Mock()

    class TestAgent(agent.Agent):
        """Helper class to test the max processing depth limit implementation."""

        def process(self, message: agent_message.Message) -> None:
            pass

        def on_max_depth_process_reached(self, message: agent_message.Message) -> None:
            on_max_depth_process_reached_mock(message)

    agent_definition = agent_definitions.AgentDefinition(
        name="agentX",
        out_selectors=["v3.report.vulnerability"],
    )
    agent_settings = runtime_definitions.AgentSettings(
        key="some_key",
        depth_processing_limit=3,
    )
    test_agent = TestAgent(
        agent_definition=agent_definition, agent_settings=agent_settings
    )
    actual_message = agent_message.Message.from_data(
        "v3.healthcheck.ping",
        {
            "body": "Hello, can you hear me?",
        },
    )
    control_message = agent_message.Message.from_data(
        "v3.control",
        {
            "control": {"agents": ["agent1", "agent2"]},
            "message": actual_message.raw,
        },
    )

    test_agent.process_message(
        f"v3.healthcheck.ping.{uuid.uuid4()}", control_message.raw
    )

    assert on_max_depth_process_reached_mock.called is False


def testProcessMessage_whenProcessingDepthLimitIsSetFromDefaultProtoValue_callbackNotCalled(
    agent_run_mock: agent_testing.AgentRunInstance, mocker: plugin.MockerFixture
) -> None:
    """When processing depth limit is not set, the proto default value is 0,
    the agent behavior must not trigger a callback."""

    on_max_depth_process_reached_mock = mocker.Mock()

    class TestAgent(agent.Agent):
        """Helper class to test the max processing depth limit implementation."""

        def process(self, message: agent_message.Message) -> None:
            pass

        def on_max_depth_process_reached(self, message: agent_message.Message) -> None:
            on_max_depth_process_reached_mock(message)

    agent_definition = agent_definitions.AgentDefinition(
        name="agentX",
        out_selectors=["v3.report.vulnerability"],
    )
    agent_settings = runtime_definitions.AgentSettings.from_proto(
        runtime_definitions.AgentSettings(
            key="some_key",
        ).to_raw_proto()
    )
    test_agent = TestAgent(
        agent_definition=agent_definition, agent_settings=agent_settings
    )
    actual_message = agent_message.Message.from_data(
        "v3.healthcheck.ping",
        {
            "body": "Hello, can you hear me?",
        },
    )
    control_message = agent_message.Message.from_data(
        "v3.control",
        {
            "control": {"agents": ["agent1", "agent2", "agent3", "agent4"]},
            "message": actual_message.raw,
        },
    )

    test_agent.process_message(
        f"v3.report.vulnerability.{uuid.uuid4()}", control_message.raw
    )

    assert on_max_depth_process_reached_mock.called is False


def testProcessMessage_whenProcessingDepthLimitIsReached_dropMessage(
    agent_run_mock: agent_testing.AgentRunInstance, mocker: plugin.MockerFixture
) -> None:
    """When processing depth limit is set and the limit is reached, the message should be dropped."""

    process_mock = mocker.Mock()
    on_max_depth_process_reached_mock = mocker.Mock()

    class TestAgent(agent.Agent):
        """Helper class to test the max processing depth limit implementation."""

        def process(self, message: agent_message.Message) -> None:
            process_mock(message)

        def on_max_depth_process_reached(self, message: agent_message.Message) -> None:
            on_max_depth_process_reached_mock(message)

    agent_definition = agent_definitions.AgentDefinition(
        name="agentX",
        out_selectors=["v3.report.vulnerability"],
    )
    agent_settings = runtime_definitions.AgentSettings(
        key="some_key",
        depth_processing_limit=3,
    )
    test_agent = TestAgent(
        agent_definition=agent_definition, agent_settings=agent_settings
    )
    actual_message = agent_message.Message.from_data(
        "v3.healthcheck.ping",
        {
            "body": "Hello, can you hear me?",
        },
    )
    control_message = agent_message.Message.from_data(
        "v3.control",
        {
            "control": {"agents": ["agent1", "agent2", "agent3", "agent4"]},
            "message": actual_message.raw,
        },
    )

    test_agent.process_message(
        f"v3.healthcheck.ping.{uuid.uuid4()}", control_message.raw
    )

    assert on_max_depth_process_reached_mock.called is True
    assert process_mock.called is False


def testProcessMessage_whenAgentIsAccepted_shouldProcessMessage(
    agent_run_mock: agent_testing.AgentRunInstance, mocker: plugin.MockerFixture
) -> None:
    """When the agent is in the list of accepted agents, message should be processed."""

    process_mock = mocker.Mock()

    class TestAgent(agent.Agent):
        """Helper class to test the accepted agents implementation."""

        def process(self, message: agent_message.Message) -> None:
            process_mock(message)

    agent_definition = agent_definitions.AgentDefinition(
        name="main_agent",
        out_selectors=["v3.report.vulnerability"],
    )
    agent_settings = runtime_definitions.AgentSettings(
        key="agent/org/main_agent",
        accepted_agents=["agent1", "agent2", "agent3"],
    )
    test_agent = TestAgent(
        agent_definition=agent_definition, agent_settings=agent_settings
    )
    actual_message = agent_message.Message.from_data(
        "v3.healthcheck.ping",
        {
            "body": "Hello, can you process me?",
        },
    )
    control_message = agent_message.Message.from_data(
        "v3.control",
        {
            "control": {"agents": ["agent4", "agent5", "agent2"]},
            "message": actual_message.raw,
        },
    )

    test_agent.process_message(
        f"v3.healthcheck.ping.{uuid.uuid4()}", control_message.raw
    )

    assert process_mock.called is True


def testProcessMessage_whenAgentNotAccepted_shouldNotProcessMessage(
    agent_run_mock: agent_testing.AgentRunInstance, mocker: plugin.MockerFixture
) -> None:
    """When the agent is not in the list of accepted agents, the message should not be processed."""

    process_mock = mocker.Mock()

    class TestAgent(agent.Agent):
        """Helper class to test the accepted agents implementation."""

        def process(self, message: agent_message.Message) -> None:
            process_mock(message)

    agent_definition = agent_definitions.AgentDefinition(
        name="main_agent",
        out_selectors=["v3.report.vulnerability"],
    )
    agent_settings = runtime_definitions.AgentSettings(
        key="agent/org/main_agent",
        accepted_agents=["agent1", "agent2", "agent3"],
    )
    test_agent = TestAgent(
        agent_definition=agent_definition, agent_settings=agent_settings
    )
    actual_message = agent_message.Message.from_data(
        "v3.healthcheck.ping",
        {
            "body": "Hello, can you process me?",
        },
    )
    control_message = agent_message.Message.from_data(
        "v3.control",
        {
            "control": {"agents": ["agent4", "agent5", "agent6"]},
            "message": actual_message.raw,
        },
    )

    test_agent.process_message(
        f"v3.healthcheck.ping.{uuid.uuid4()}", control_message.raw
    )

    assert process_mock.called is False


def testProcessMessage_whenAcceptedAgentsNotSet_shouldProcessMessage(
    agent_run_mock: agent_testing.AgentRunInstance, mocker: plugin.MockerFixture
) -> None:
    """When the accepted agents is not set, the message should be processed."""

    process_mock = mocker.Mock()

    class TestAgent(agent.Agent):
        """Helper class to test that the message is processed when the accepted agents is not set."""

        def process(self, message: agent_message.Message) -> None:
            process_mock(message)

    agent_definition = agent_definitions.AgentDefinition(
        name="main_agent",
        out_selectors=["v3.report.vulnerability"],
    )
    agent_settings = runtime_definitions.AgentSettings(
        key="agent/org/main_agent",
    )
    test_agent = TestAgent(
        agent_definition=agent_definition, agent_settings=agent_settings
    )
    actual_message = agent_message.Message.from_data(
        "v3.healthcheck.ping",
        {
            "body": "Hello, can you process me?",
        },
    )
    control_message = agent_message.Message.from_data(
        "v3.control",
        {
            "control": {"agents": ["agent4", "agent5", "agent6"]},
            "message": actual_message.raw,
        },
    )

    test_agent.process_message(
        f"v3.healthcheck.ping.{uuid.uuid4()}", control_message.raw
    )

    assert process_mock.called is True


def testProcessMessage_whenAgentSettingsInSelectorsNotSet_shouldUseAgentDefinitionInSelectors(
    agent_run_mock: agent_testing.AgentRunInstance, mocker: plugin.MockerFixture
) -> None:
    """When the agent settings in selectors are not set, the agent definition in selectors should be used."""

    process_mock = mocker.Mock()

    class TestAgent(agent.Agent):
        """Helper class to test that the agent settings in selectors are used when not set."""

        def process(self, message: agent_message.Message) -> None:
            process_mock(message)

    agent_definition = agent_definitions.AgentDefinition(
        name="main_agent",
        in_selectors=["v3.healthcheck.ping", "v3.asset.file"],
        out_selectors=["v3.report.vulnerability"],
    )
    agent_settings = runtime_definitions.AgentSettings(
        key="agent/org/main_agent",
    )
    test_agent = TestAgent(
        agent_definition=agent_definition, agent_settings=agent_settings
    )
    actual_message = agent_message.Message.from_data(
        "v3.healthcheck.ping",
        {
            "body": "Hello, can you process me?",
        },
    )
    control_message = agent_message.Message.from_data(
        "v3.control",
        {
            "control": {"agents": ["agent4", "agent5", "agent6"]},
            "message": actual_message.raw,
        },
    )

    test_agent.process_message(
        f"v3.healthcheck.ping.{uuid.uuid4()}", control_message.raw
    )

    assert len(test_agent.in_selectors) == 2
    assert "v3.healthcheck.ping" in test_agent.in_selectors
    assert "v3.asset.file" in test_agent.in_selectors
    assert process_mock.called is True


def testProcessMessage_whenAgentSettingsInSelectorsSet_shouldUseAgentSettingsInSelectors(
    agent_run_mock: agent_testing.AgentRunInstance, mocker: plugin.MockerFixture
) -> None:
    """When the agent settings in selectors are set, the agent settings in selectors should be used."""

    process_mock = mocker.Mock()

    class TestAgent(agent.Agent):
        """Helper class to test that the agent settings in selectors are used when set."""

        def process(self, message: agent_message.Message) -> None:
            process_mock(message)

    agent_definition = agent_definitions.AgentDefinition(
        name="main_agent",
        in_selectors=["v3.healthcheck.ping", "v3.asset.file"],
        out_selectors=["v3.report.vulnerability"],
    )
    agent_settings = runtime_definitions.AgentSettings(
        key="agent/org/main_agent",
        in_selectors=["v3.healthcheck.ping", "v3.asset.file.ios.ipa"],
    )
    test_agent = TestAgent(
        agent_definition=agent_definition, agent_settings=agent_settings
    )
    actual_message = agent_message.Message.from_data(
        "v3.healthcheck.ping",
        {
            "body": "Hello, can you process me?",
        },
    )
    control_message = agent_message.Message.from_data(
        "v3.control",
        {
            "control": {"agents": ["agent4", "agent5", "agent6"]},
            "message": actual_message.raw,
        },
    )

    test_agent.process_message(
        f"v3.healthcheck.ping.{uuid.uuid4()}", control_message.raw
    )

    assert len(test_agent.in_selectors) == 2
    assert "v3.healthcheck.ping" in test_agent.in_selectors
    assert "v3.asset.file.ios.ipa" in test_agent.in_selectors
    assert process_mock.called is True


def testEmit_whenOutSelectorIsNotExact_emitsMessage(
    agent_run_mock: agent_testing.AgentRunInstance,
) -> None:
    """Test emit when out-selector is the message parent."""

    class TestAgent(agent.Agent):
        """Helper class to test OpenTelemetry mixin implementation."""

        def process(self, message: agent_message.Message) -> None:
            pass

    agent_definition = agent_definitions.AgentDefinition(
        name="some_name", out_selectors=["v3.report"]
    )
    agent_settings = runtime_definitions.AgentSettings(
        key="some_key",
    )
    test_agent = TestAgent(
        agent_definition=agent_definition, agent_settings=agent_settings
    )

    test_agent.emit(
        "v3.report.vulnerability",
        {
            "title": "some_title",
            "technical_detail": "some_detail",
            "risk_rating": "MEDIUM",
        },
    )

    assert len(agent_run_mock.control_messages) > 0
    assert agent_run_mock.control_messages[0].data["control"]["agents"] == ["some_name"]


def testAgentMixin_whenServiceNameInSettings_usesItAsName(
    agent_mock: list[agent_message.Message],
) -> None:
    """When service_name is set in AgentSettings, it must be used as the MQ queue name so each
    named instance gets its own queue and receives all published messages instead of competing
    with sibling instances on a shared queue."""

    class TestAgent(agent.Agent):
        """Test agent."""

    test_agent = TestAgent(
        agent_definitions.AgentDefinition(
            name="test_agent", in_selectors=["v3.asset.link"]
        ),
        runtime_definitions.AgentSettings(
            key="agent/ostorlab/test_agent",
            bus_url="amqp://guest:guest@localhost:5672/",
            bus_exchange_topic="ostorlab_test",
            healthcheck_port=5301,
            service_name="named_instance_1",
        ),
    )

    assert test_agent.mq_name == "named_instance_1"


def testAgentMixin_whenServiceNameNotInSettings_usesAgentDefinitionNameAsFallback(
    agent_mock: list[agent_message.Message],
) -> None:
    """Without service_name in AgentSettings the queue name falls back to the agent definition name."""

    class TestAgent(agent.Agent):
        """Test agent."""

    test_agent = TestAgent(
        agent_definitions.AgentDefinition(
            name="test_agent", in_selectors=["v3.asset.link"]
        ),
        runtime_definitions.AgentSettings(
            key="agent/ostorlab/test_agent",
            bus_url="amqp://guest:guest@localhost:5672/",
            bus_exchange_topic="ostorlab_test",
            healthcheck_port=5301,
        ),
    )

    assert test_agent.mq_name == "test_agent"


def testEmit_whenOutSelectorIsNotParent_dontEmitMessage(
    agent_run_mock: agent_testing.AgentRunInstance,
) -> None:
    """Test emit when out-selector is not the message parent."""

    class TestAgent(agent.Agent):
        """Helper class to test OpenTelemetry mixin implementation."""

        def process(self, message: agent_message.Message) -> None:
            pass

    agent_definition = agent_definitions.AgentDefinition(
        name="some_name", out_selectors=["v3.report.vulnerability.xxx"]
    )
    agent_settings = runtime_definitions.AgentSettings(
        key="some_key",
    )
    test_agent = TestAgent(
        agent_definition=agent_definition, agent_settings=agent_settings
    )

    with pytest.raises(agent.NonListedMessageSelectorError):
        test_agent.emit(
            "v3.report.vulnerability",
            {
                "title": "some_title",
                "technical_detail": "some_detail",
                "risk_rating": "MEDIUM",
            },
        )


def testEmitRaw_whenMessagePriorityIsProvided_forwardsPriorityToMqSendMessage(
    mocker: plugin.MockerFixture,
) -> None:
    """Test that emit_raw forwards the message priority to MQ publishing."""

    class TestAgent(agent.Agent):
        """Test agent."""

    test_agent = TestAgent(
        agent_definitions.AgentDefinition(
            name="some_name", out_selectors=["v3.report.vulnerability"]
        ),
        runtime_definitions.AgentSettings(
            key="some_key",
        ),
    )
    mock_send_message = mocker.patch.object(test_agent, "mq_send_message")

    test_agent.emit_raw(
        "v3.report.vulnerability",
        b"some raw payload",
        message_priority=7,
    )

    mock_send_message.assert_called_once()
    assert mock_send_message.call_args.kwargs["message_priority"] == 7
    assert mock_send_message.call_args.args[0].startswith("v3.report.vulnerability.")
    assert mock_send_message.call_args.args[1] is not None


def testSetupLogging_whenMachineNameIsProvided_addsToLogMetadata(
    mocker: plugin.MockerFixture,
) -> None:
    """Test the _setup_logging directly."""
    mock_client_instance = mocker.MagicMock()
    mocker.patch("google.cloud.logging.Client", return_value=mock_client_instance)
    mocker.patch(
        "google.oauth2.service_account.Credentials.from_service_account_info",
        return_value=mocker.MagicMock(),
    )
    fake_cred = base64.b64encode(
        json.dumps({"type": "service_account"}).encode()
    ).decode()
    mocker.patch.dict("os.environ", {"GCP_LOGGING_CREDENTIAL": fake_cred})

    agent._setup_logging(
        hostname="test_host",
        host_hostname="test_machine",
        agent_key="test_key",
        agent_version="test_version",
        universe="test_universe",
    )

    mock_client_instance.setup_logging.assert_called_once()
    call_args = mock_client_instance.setup_logging.call_args
    labels = call_args.kwargs.get("labels", {})
    assert labels["host_hostname"] == "test_machine"
    assert labels["hostname"] == "test_host"
    assert labels["universe"] == "test_universe"
    assert labels["agent_key"] == "test_key"
    assert labels["agent_version"] == "test_version"


def testSetupLogging_whenServiceNameIsProvided_labelIncludesServiceName(
    mocker: plugin.MockerFixture,
) -> None:
    """service_name must appear in GCP logging labels when set."""
    mock_client_instance = mocker.MagicMock()
    mocker.patch("google.cloud.logging.Client", return_value=mock_client_instance)
    mocker.patch(
        "google.oauth2.service_account.Credentials.from_service_account_info",
        return_value=mocker.MagicMock(),
    )
    fake_cred = base64.b64encode(
        json.dumps({"type": "service_account"}).encode()
    ).decode()
    mocker.patch.dict("os.environ", {"GCP_LOGGING_CREDENTIAL": fake_cred})

    agent._setup_logging(
        hostname="host1",
        agent_key="agent/org/test",
        agent_version="1.0",
        universe="universe42",
        service_name="my_swarm_service",
    )

    labels = mock_client_instance.setup_logging.call_args.kwargs["labels"]
    assert labels["service_name"] == "my_swarm_service"


def testSetupLogging_whenServiceNameIsNotProvided_labelDoesNotIncludeServiceName(
    mocker: plugin.MockerFixture,
) -> None:
    """service_name label must be absent when not set."""
    mock_client_instance = mocker.MagicMock()
    mocker.patch("google.cloud.logging.Client", return_value=mock_client_instance)
    mocker.patch(
        "google.oauth2.service_account.Credentials.from_service_account_info",
        return_value=mocker.MagicMock(),
    )
    fake_cred = base64.b64encode(
        json.dumps({"type": "service_account"}).encode()
    ).decode()
    mocker.patch.dict("os.environ", {"GCP_LOGGING_CREDENTIAL": fake_cred})

    agent._setup_logging(
        hostname="host1",
        agent_key="agent/org/test",
        agent_version="1.0",
        universe="universe42",
    )

    labels = mock_client_instance.setup_logging.call_args.kwargs["labels"]
    assert "service_name" not in labels


def testSetupLogging_whenMachineNameIsNotProvided_labelDoesNotIncludeMachineName(
    mocker: plugin.MockerFixture,
) -> None:
    """host_hostname label must be absent when not set."""
    mock_client_instance = mocker.MagicMock()
    mocker.patch("google.cloud.logging.Client", return_value=mock_client_instance)
    mocker.patch(
        "google.oauth2.service_account.Credentials.from_service_account_info",
        return_value=mocker.MagicMock(),
    )
    fake_cred = base64.b64encode(
        json.dumps({"type": "service_account"}).encode()
    ).decode()
    mocker.patch.dict("os.environ", {"GCP_LOGGING_CREDENTIAL": fake_cred})

    agent._setup_logging(
        hostname="host1",
        agent_key="agent/org/test",
        agent_version="1.0",
        universe="universe42",
    )

    labels = mock_client_instance.setup_logging.call_args.kwargs["labels"]
    assert "host_hostname" not in labels


class DeliveryAgent(agent.Agent):
    """Real message handler recording attempts and cleanup for delivery tests."""

    def __init__(
        self, settings: runtime_definitions.AgentSettings, failures: int = 0
    ) -> None:
        super().__init__(
            agent_definitions.AgentDefinition(
                name="delivery_agent", in_selectors=["v3.healthcheck.ping"]
            ),
            settings,
        )
        self.failures = failures
        self.attempts: list[str] = []
        self.cleanups = 0

    def process(self, message: agent_message.Message) -> None:
        body = typing.cast(str, message.data["body"])
        self.attempts.append(body)
        if body == "fail" and self.failures > 0:
            self.failures -= 1
            raise ValueError("handler failed")

    def process_cleanup(self) -> None:
        self.cleanups += 1


def _delivery_body(body: str, agents: tuple[str, ...] = ()) -> bytes:
    message = agent_message.Message.from_data("v3.healthcheck.ping", {"body": body})
    return agent_message.Message.from_data(
        "v3.control", {"control": {"agents": list(agents)}, "message": message.raw}
    ).raw


def _incoming_delivery(
    transport: mock.AsyncMock,
    body: bytes,
    redelivered: bool = False,
    delivery_tag: int = 1,
) -> aio_pika.IncomingMessage:
    return aio_pika.IncomingMessage(
        aiormq_abc.DeliveredMessage(
            delivery=commands.Basic.Deliver(
                delivery_tag=delivery_tag,
                routing_key="v3.healthcheck.ping.delivery",
                redelivered=redelivered,
            ),
            header=header.ContentHeader(),
            body=body,
            channel=transport,
        )
    )


type DeliveryConsumer = tuple[
    DeliveryAgent,
    collections.abc.Callable[
        [aio_pika.IncomingMessage], collections.abc.Awaitable[None]
    ],
    mock.AsyncMock,
]


@pytest_asyncio.fixture
async def delivery_consumer(
    mocker: plugin.MockerFixture,
) -> collections.abc.AsyncIterator[DeliveryConsumer]:
    """Register the real consumer with a mocked AMQP transport."""
    mocker.patch("ostorlab.agent.mixins.agent_healthcheck_mixin.serving.make_server")
    mocker.patch("ostorlab.agent.agent.signal.signal")
    connection = mocker.AsyncMock()
    channel = connection.channel.return_value
    transport = mocker.AsyncMock()
    transport.is_closed = False
    mocker.patch("aio_pika.connect_robust", return_value=connection)
    client = DeliveryAgent(
        runtime_definitions.AgentSettings(key="delivery"), failures=2
    )
    try:
        await client.mq_run()
        channel.declare_queue.return_value.consume.assert_awaited_once()
        callback = channel.declare_queue.return_value.consume.call_args.args[0]
        assert channel.declare_queue.return_value.consume.call_args.kwargs == {
            "no_ack": False
        }
        yield client, callback, transport
    finally:
        client._executor.shutdown(wait=True)


@pytest.mark.asyncio
@pytest.mark.parametrize("redelivered", [False, True])
async def testAgentConsumer_whenHandlerFails_rejectsWithBoundedRedeliveryAndKeepsConsuming(
    delivery_consumer: DeliveryConsumer,
    mocker: plugin.MockerFixture,
    redelivered: bool,
) -> None:
    client, callback, transport = delivery_consumer
    handler = logging.StreamHandler(io.StringIO())
    handler.setLevel(logging.CRITICAL)
    flush = mocker.spy(handler, "flush")
    mocker.patch.object(agent.logger, "handlers", [handler])
    failed = _incoming_delivery(transport, _delivery_body("fail"), redelivered)

    with pytest.raises(ValueError, match="handler failed"):
        await callback(failed)

    transport.basic_ack.assert_not_awaited()
    transport.basic_reject.assert_awaited_once_with(
        delivery_tag=1, requeue=redelivered is False
    )
    assert failed.processed is True
    assert client.cleanups == 1
    flush.assert_called_once_with()

    await callback(
        _incoming_delivery(transport, _delivery_body("healthy"), delivery_tag=2)
    )

    transport.basic_ack.assert_awaited_once_with(delivery_tag=2, multiple=False)
    assert client.attempts == ["fail", "healthy"]
    assert client.cleanups == 2
    assert flush.call_count == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("skip", ["success", "sender", "cyclic", "depth"])
async def testAgentConsumer_whenProcessingSucceedsOrIsIntentionallySkipped_acknowledges(
    delivery_consumer: DeliveryConsumer,
    skip: str,
) -> None:
    client, callback, transport = delivery_consumer
    if skip == "sender":
        client.accepted_agents = ["trusted"]
    elif skip == "cyclic":
        client.cyclic_processing_limit = 1
    elif skip == "depth":
        client.depth_processing_limit = 1

    await callback(
        _incoming_delivery(transport, _delivery_body("healthy", (client.name,)))
    )

    transport.basic_ack.assert_awaited_once_with(delivery_tag=1, multiple=False)
    transport.basic_reject.assert_not_awaited()
    assert client.attempts == (["healthy"] if skip == "success" else [])


@pytest.fixture
def delivery_broker() -> collections.abc.Iterator[str]:
    """Provide a uniquely named RabbitMQ service and remove only its resources."""
    resource_name = f"oxo_delivery_{uuid.uuid4().hex}"
    docker_client = docker.from_env()
    network = docker_client.networks.create(resource_name, driver="overlay")
    service = None
    try:
        service = typing.cast(
            collections.abc.Callable[..., docker_services.Service],
            docker_client.services.create,
        )(
            mq.MQ_IMAGE,
            name=resource_name,
            networks=[network.id],
            endpoint_spec=typing.cast(
                collections.abc.Callable[..., docker.types.EndpointSpec],
                docker.types.EndpointSpec,
            )(ports={0: 5672}),
            env=["RABBITMQ_SERVER_ADDITIONAL_ERL_ARGS=+S 2:2"],
            mounts=[
                docker.types.Mount(
                    target="/var/lib/rabbitmq", source=None, type="tmpfs"
                )
            ],
        )
        deadline = time.monotonic() + 30
        while len(service.attrs.get("Endpoint", {}).get("Ports", [])) == 0:
            if time.monotonic() >= deadline:
                raise TimeoutError("RabbitMQ service did not publish its AMQP port")
            time.sleep(0.1)
            service.reload()
        port = service.attrs["Endpoint"]["Ports"][0]["PublishedPort"]
        yield f"amqp://guest:guest@127.0.0.1:{port}/"
    finally:
        if service is not None:
            typing.cast(collections.abc.Callable[[], None], service.remove)()
        deadline = time.monotonic() + 30
        while True:
            try:
                network.remove()
                break
            except docker.errors.APIError:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(0.1)
        docker_client.close()


@pytest.mark.asyncio
@pytest.mark.docker
@pytest.mark.timeout(90)
async def testAgentConsumer_whenRabbitMqHandlerFailsOnce_redeliversThenAcknowledges(
    delivery_broker: str, mocker: plugin.MockerFixture
) -> None:
    mocker.patch("ostorlab.agent.mixins.agent_healthcheck_mixin.serving.make_server")
    mocker.patch("ostorlab.agent.agent.signal.signal")
    deadline = time.monotonic() + 60
    while True:
        try:
            connection = await aio_pika.connect_robust(delivery_broker, timeout=1)
            break
        except (OSError, aio_pika.exceptions.AMQPConnectionError):
            if time.monotonic() >= deadline:
                raise
            await asyncio.sleep(0.2)

    async with connection:
        acknowledge = mocker.spy(aio_pika.IncomingMessage, "ack")
        reject = mocker.spy(aio_pika.IncomingMessage, "reject")
        mocker.patch("aio_pika.connect_robust", return_value=connection)
        client = DeliveryAgent(
            runtime_definitions.AgentSettings(
                key="delivery",
                bus_url=delivery_broker,
                bus_exchange_topic="delivery_test",
            ),
            failures=1,
        )
        try:
            await client.mq_run()
            channel = await connection.channel()
            exchange = await channel.get_exchange("delivery_test")
            for body in ("fail", "healthy"):
                await exchange.publish(
                    aio_pika.Message(body=_delivery_body(body)),
                    routing_key="v3.healthcheck.ping.delivery",
                )
            async with asyncio.timeout(10):
                while len(acknowledge.spy_return_list) < 2:
                    await asyncio.sleep(0.01)
            await channel.close()
            channel = await connection.channel()
            queue = await channel.declare_queue("delivery_agent_queue", passive=True)
            assert client.attempts == ["fail", "fail", "healthy"]
            assert client.cleanups == 3
            assert [
                call.args[0].redelivered for call in acknowledge.call_args_list
            ] == [
                True,
                False,
            ]
            assert reject.call_count == 1
            assert reject.call_args.args[0].redelivered is False
            assert reject.call_args.kwargs == {"requeue": True}
            assert queue.declaration_result.message_count == 0
            assert queue.declaration_result.consumer_count == 1
        finally:
            await client._channel_pool.close()
            await client._connection_pool.close()
            client._executor.shutdown(wait=True)
