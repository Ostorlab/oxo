"""Agent class unit tests."""
import datetime
import json
import logging
import multiprocessing as mp
import pathlib
import time
import uuid
import signal
import sys
import os

import pytest
from pytest_mock import plugin

from ostorlab.agent import agent
from ostorlab.agent import definitions as agent_definitions
from ostorlab.agent.message import message as agent_message
from ostorlab.runtimes import definitions as runtime_definitions
from ostorlab.testing import agent as agent_testing
from ostorlab.utils import defintions as utils_definitions
from ostorlab.utils import system

logger = logging.getLogger(__name__)


@pytest.mark.timeout(60)
@pytest.mark.docker
def testAgent_whenAnAgentSendAMessageFromStartAgent_listeningToMessageReceivesIt(
    mq_service, redis_service
):
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
                {"body": f"from test agent at {datetime.datetime.now()}"},
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


def testAgentMain_whenPassedArgsAreValid_runsAgent(mocker):
    """Test agent main with proper arguments, agent runs."""

    class SampleAgent(agent.Agent):
        """Sample agent"""

    mocker.patch("ostorlab.agent.agent.Agent.__init__", return_value=None)
    mocker.patch("ostorlab.agent.agent.Agent.run", return_value=None)
    mocker.patch.object(
        agent,
        "AGENT_DEFINITION_PATH",
        str(pathlib.Path(__file__).parent / "dummyagent.yaml"),
    )

    SampleAgent.main(
        ["--settings", str(pathlib.Path(__file__).parent / "settings.binproto")]
    )

    SampleAgent.run.assert_called()
    SampleAgent.__init__.assert_called()


def testAgentMain_withNonExistingFile_exits(mocker):
    """Test agent when missing definition or settings files to ensure the command exits."""

    class SampleAgent(agent.Agent):
        """Sample agent"""

    mocker.patch("ostorlab.agent.agent.Agent.__init__", return_value=None)
    mocker.patch("ostorlab.agent.agent.Agent.run", return_value=None)
    with pytest.raises(SystemExit) as wrapper_exception:
        SampleAgent.main(["--definition", "random", "--settings", "random"])

        SampleAgent.run.assert_not_called()
        SampleAgent.__init__.assert_not_called()
        assert wrapper_exception.type == SystemExit
        assert wrapper_exception.value.code == 42


def testAgent_withDefaultAndSettingsArgs_returnsExpectedArgs(agent_mock):
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


@pytest.mark.xfail(reason="OS-5119: Awaiting deprecation.")
def testAgent_withArgMissingFromDefinition_raisesException(agent_mock):
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
    agent_run_mock: agent_testing.AgentRunInstance, mocker
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
    agent_run_mock: agent_testing.AgentRunInstance, mocker
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

    test_agent.process_message(
        f"v3.healthcheck.ping.{uuid.uuid4()}", control_message.raw
    )

    assert logger_error.call_count == 3
    assert "System Info: %s" in logger_error.call_args_list[0][0][0]
    assert (
        isinstance(logger_error.call_args_list[0][0][1], system.SystemLoadInfo) is True
    )
    assert (
        isinstance(logger_error.call_args_list[1][0][1], agent_message.Message) is True
    )
    assert logger_error.call_args_list[1][0][1].selector == "v3.healthcheck.ping"
    assert (
        logger_error.call_args_list[1][0][1].data["body"] == "Hello, can you hear me?"
    )
    assert isinstance(logger_error.call_args_list[2][0][1], ValueError) is True
    assert "some error" in logger_error.call_args_list[2][0][1].args[0]


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

    test_agent.process_message(
        f"v3.healthcheck.ping.{uuid.uuid4()}", control_message.raw
    )

    assert logger_error.call_count == 2
    assert (
        isinstance(logger_error.call_args_list[0][0][1], agent_message.Message) is True
    )
    assert logger_error.call_args_list[0][0][1].selector == "v3.healthcheck.ping"
    assert (
        logger_error.call_args_list[0][0][1].data["body"] == "Hello, can you hear me?"
    )
    assert isinstance(logger_error.call_args_list[1][0][1], ValueError) is True
    assert "some error" in logger_error.call_args_list[1][0][1].args[0]


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

        def __init__(self, agent_definition, agent_settings, mp_event) -> None:
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

    def run_agent(agent_definition, agent_settings, message, mp_event):
        """method responsible for running the test agent inside a process."""
        test_agent = TestAgent(
            agent_definition=agent_definition,
            agent_settings=agent_settings,
            mp_event=mp_event,
        )
        test_agent.process(message)

    agent_process = mp.Process(
        target=run_agent,
        args=(
            agent_definition,
            agent_settings,
            ping_message,
            mp_event,
        ),
        daemon=False,
    )
    mp_event.clear()
    agent_process.start()
    time.sleep(3)
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
