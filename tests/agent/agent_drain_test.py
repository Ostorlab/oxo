"""SIGTERM exercises the real SDK loop and executor without an external broker."""

import asyncio
import multiprocessing
import os
import signal
import sys
from multiprocessing import synchronize
from unittest import mock

import aio_pika
import pytest

from ostorlab.agent import agent
from ostorlab.agent import definitions as agent_definitions
from ostorlab.runtimes import definitions as runtime_definitions


def _run_busy_agent(
    started: synchronize.Event,
    release: synchronize.Event,
    acknowledged: synchronize.Event,
    cleaned: synchronize.Event,
    phase: str,
) -> None:
    class BusyAgent(agent.Agent):
        def start_healthcheck(self) -> None:
            pass

        def stop_healthcheck(self) -> None:
            pass

        async def mq_init(self, delete_queue_first: bool = False) -> None:
            del delete_queue_first

        def start(self) -> None:
            if phase == "startup":
                started.set()
                assert release.wait(10)

        async def mq_run(self, delete_queue_first: bool = False) -> None:
            del delete_queue_first
            assert phase != "startup"
            if phase == "idle":
                started.set()
                return
            message = mock.Mock(spec=aio_pika.abc.AbstractIncomingMessage)
            message.body = b"risk"
            message.routing_key = "risk"
            context = mock.AsyncMock()

            async def acknowledge(*args: object) -> None:
                del args
                acknowledged.set()

            context.__aexit__.side_effect = acknowledge
            message.process.return_value = context
            self._callback = asyncio.create_task(self._mq_process_message(message))

        def process_message(self, selector: str, message: bytes) -> None:
            del selector, message
            started.set()
            assert release.wait(10)

        def at_exit(self) -> None:
            if phase == "busy":
                assert acknowledged.is_set() is True
            cleaned.set()

    instance = BusyAgent(
        agent_definitions.AgentDefinition(name="drain-test", in_selectors=["risk"]),
        runtime_definitions.AgentSettings(key="drain-test", healthcheck_port=0),
    )
    instance.run()


@pytest.mark.skipif(sys.platform == "win32", reason="Requires POSIX signals")
@pytest.mark.parametrize("phase", ["busy", "startup", "idle"])
def testAgent_sigterm_finishesAndAcknowledgesBeforeCleanup(phase: str) -> None:
    context = multiprocessing.get_context("spawn")
    started = context.Event()
    release = context.Event()
    acknowledged = context.Event()
    cleaned = context.Event()
    process = context.Process(
        target=_run_busy_agent, args=(started, release, acknowledged, cleaned, phase)
    )
    process.start()
    try:
        assert started.wait(10)
        assert process.pid is not None
        os.kill(process.pid, signal.SIGTERM)
        if phase != "idle":
            assert cleaned.wait(0.1) is False
            assert process.is_alive() is True
            os.kill(process.pid, signal.SIGTERM)
        release.set()
        process.join(10)
        assert process.exitcode == 0
        assert acknowledged.is_set() is (phase == "busy")
        assert cleaned.is_set() is True
    finally:
        release.set()
        if process.is_alive() is True:
            process.kill()
        process.join(5)


def _run_standalone_agent(
    started: synchronize.Event, cleaned: synchronize.Event
) -> None:
    class StandaloneAgent(agent.Agent):
        def start_healthcheck(self) -> None:
            pass

        def stop_healthcheck(self) -> None:
            pass

        async def mq_init(self, delete_queue_first: bool = False) -> None:
            del delete_queue_first

        def start(self) -> None:
            started.set()
            assert cleaned.wait(10)

        def at_exit(self) -> None:
            assert cleaned.is_set() is False
            cleaned.set()

    StandaloneAgent(
        agent_definitions.AgentDefinition(name="standalone-drain"),
        runtime_definitions.AgentSettings(key="standalone-drain", healthcheck_port=0),
    ).run()


@pytest.mark.skipif(sys.platform == "win32", reason="Requires POSIX signals")
def testAgent_standaloneSigterm_cleanupStopsLongRunningStart() -> None:
    context = multiprocessing.get_context("spawn")
    started = context.Event()
    cleaned = context.Event()
    process = context.Process(target=_run_standalone_agent, args=(started, cleaned))
    process.start()
    try:
        assert started.wait(10)
        assert process.pid is not None
        os.kill(process.pid, signal.SIGTERM)
        process.join(3)
        assert process.exitcode == 0
        assert cleaned.is_set() is True
    finally:
        if process.is_alive() is True:
            process.kill()
        process.join(5)


class _LateSignalAgent(agent.Agent):
    def __init__(self) -> None:
        self.cleanup_calls: int = 0
        super().__init__(
            agent_definitions.AgentDefinition(name="late-signal"),
            runtime_definitions.AgentSettings(key="late-signal", healthcheck_port=0),
        )

    def start_healthcheck(self) -> None:
        pass

    def stop_healthcheck(self) -> None:
        pass

    async def mq_init(self, delete_queue_first: bool = False) -> None:
        del delete_queue_first

    def at_exit(self) -> None:
        self.cleanup_calls += 1


@pytest.mark.parametrize("run_first", [False, True])
def testAgent_sigtermOutsideRun_callsCleanupOnlyOnce(run_first: bool) -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    previous_handler = signal.getsignal(signal.SIGTERM)
    instance = _LateSignalAgent()
    try:
        if run_first is True:
            instance.run()
        for _ in range(2):
            with pytest.raises(SystemExit):
                instance._handle_signal(signal.SIGTERM, None)
        assert instance.cleanup_calls == 1
    finally:
        instance._executor.shutdown()
        loop.close()
        signal.signal(signal.SIGTERM, previous_handler)
        asyncio.set_event_loop(None)


def testAgent_sigtermAtLoopClose_exitsWithoutSchedulingOnClosedLoop() -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    previous_handler = signal.getsignal(signal.SIGTERM)
    instance = _LateSignalAgent()
    close_loop = loop.close

    def close_then_signal() -> None:
        close_loop()
        with pytest.raises(SystemExit):
            instance._handle_signal(signal.SIGTERM, None)

    try:
        with mock.patch.object(loop, "close", side_effect=close_then_signal):
            instance.run()
        assert loop.is_closed() is True
        assert instance.cleanup_calls == 1
    finally:
        instance._executor.shutdown()
        close_loop()
        signal.signal(signal.SIGTERM, previous_handler)
        asyncio.set_event_loop(None)
