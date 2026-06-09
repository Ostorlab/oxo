"""Agent class unit tests."""

import base64
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
from ostorlab.utils import definitions as utils_definitions
from ostorlab.utils import system

logger = logging.getLogger(__name__)


def _run_agent_until_signal(
    agent_definition: agent_definitions.AgentDefinition,
    agent_settings_proto: bytes,
    message: agent_message.Message,
    mp_event,
) -> None:
    """Run the test agent in a separate process until it is terminated."""

    agent_settings = runtime_definitions.AgentSettings.from_proto(agent_settings_proto)

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

    test_agent = TestAgent(
        agent_definition=agent_definition,
        agent_settings=agent_settings,
        mp_event=mp_event,
    )
    test_agent.process(message)


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
        assert isinstance(wrapper_exception.type, SystemExit) is True
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


def testAgent_whenMaxPriorityProvided_passesItToMqMixin(mocker):
    """Test agent init passes explicit queue priority to the MQ mixin."""

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

    TestAgent(agent_definition, agent_settings, max_priority=4)

    mq_init.assert_called_once_with(
        mocker.ANY,
        name="priority_test_agent",
        keys=["v3.healthcheck.ping.#"],
        url="amqp://guest:guest@localhost:5672/",
        topic="ostorlab_test",
        max_priority=4,
    )


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
    assert "Exception: %s" in logger_error.call_args_list[1][0][0]
    assert isinstance(logger_error.call_args_list[1][0][1], ValueError) is True
    assert "some error" in logger_error.call_args_list[1][0][1].args[0]
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

    test_agent.process_message(
        f"v3.healthcheck.ping.{uuid.uuid4()}", control_message.raw
    )

    assert logger_error.call_count == 2
    assert "Exception: %s" in logger_error.call_args_list[0][0][0]
    assert isinstance(logger_error.call_args_list[0][0][1], ValueError) is True
    assert "some error" in logger_error.call_args_list[0][0][1].args[0]
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
    agent_mock,
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
    agent_mock,
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
    mocker,
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


def testSetupLogging_whenMachineNameIsProvided_addsToLogMetadata(mocker):
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
