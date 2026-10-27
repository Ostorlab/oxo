"""Real RabbitMQ and process retirement integration; requires local Docker."""

import asyncio
import collections.abc
import multiprocessing
import os
import signal
import sys
import time
from multiprocessing import synchronize

import aio_pika
import docker
import pytest

from ostorlab.agent import agent
from ostorlab.agent import definitions as agent_definitions
from ostorlab.agent.mixins import agent_mq_mixin
from ostorlab.runtimes import definitions as runtime_definitions


@pytest.fixture
def drain_broker_url() -> collections.abc.Iterator[str]:
    """Use a disposable broker with a random port bound only to loopback."""
    client = docker.from_env()
    container = client.containers.run(
        "rabbitmq:3.9-management",
        detach=True,
        user="999:999",
        ports={"5672/tcp": ("127.0.0.1", 0)},
        environment={
            "RABBITMQ_DEFAULT_USER": "drain",
            "RABBITMQ_DEFAULT_PASS": "test",
            "RABBITMQ_SERVER_ADDITIONAL_ERL_ARGS": "+S 2:2",
            "RABBITMQ_CTL_ERL_ARGS": "+S 1:1",
        },
    )
    try:
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            container.reload()
            if container.status != "running":
                pytest.fail(container.logs(tail=30).decode())
            result = container.exec_run(["rabbitmq-diagnostics", "-q", "ping"])
            if result.exit_code == 0:
                break
            time.sleep(0.2)
        else:
            pytest.fail("Isolated RabbitMQ did not become ready")
        container.reload()
        port = container.attrs["NetworkSettings"]["Ports"]["5672/tcp"][0]["HostPort"]
        yield f"amqp://drain:test@127.0.0.1:{port}/"
    finally:
        container.remove(force=True, v=True)
        client.close()


def _run_broker_worker(
    url: str,
    ready: synchronize.Event,
    started: synchronize.Event,
    release: synchronize.Event,
    acknowledged: synchronize.Event,
    cleaned: synchronize.Event,
) -> None:
    class BrokerWorker(agent.Agent):
        def start_healthcheck(self) -> None:
            pass

        def stop_healthcheck(self) -> None:
            pass

        async def mq_run(self, delete_queue_first: bool = False) -> None:
            await super().mq_run(delete_queue_first)
            ready.set()

        async def _mq_process_delivery(
            self, message: aio_pika.abc.AbstractIncomingMessage
        ) -> None:
            await super()._mq_process_delivery(message)
            acknowledged.set()

        def process_message(self, selector: str, message: bytes) -> None:
            del selector
            assert message == b"first"
            started.set()
            assert release.wait(30)

        def at_exit(self) -> None:
            assert acknowledged.is_set() is True
            cleaned.set()

    instance = BrokerWorker(
        agent_definitions.AgentDefinition(name="drain-broker", in_selectors=["risk"]),
        runtime_definitions.AgentSettings(
            key="drain-broker",
            healthcheck_port=0,
            bus_url=url,
            bus_exchange_topic="risks",
        ),
    )
    instance.run()


@pytest.mark.docker
@pytest.mark.asyncio
@pytest.mark.skipif(sys.platform == "win32", reason="Requires POSIX signals")
async def testDrain_realBroker_successorConsumesQueuedJobWhileActiveJobFinishes(
    drain_broker_url: str,
) -> None:
    context = multiprocessing.get_context("spawn")
    ready = context.Event()
    started = context.Event()
    release = context.Event()
    acknowledged = context.Event()
    cleaned = context.Event()
    worker = context.Process(
        target=_run_broker_worker,
        args=(drain_broker_url, ready, started, release, acknowledged, cleaned),
    )
    received: list[bytes] = []
    second_received = asyncio.Event()
    loop = asyncio.get_running_loop()

    class Successor(agent_mq_mixin.AgentMQMixin):
        def process_message(self, selector: str, message: bytes) -> None:
            del selector
            received.append(message)
            loop.call_soon_threadsafe(second_received.set)

    successor = Successor("drain-broker", ["risk.#"], drain_broker_url, "risks")
    worker.start()
    try:
        assert await asyncio.to_thread(ready.wait, 20)
        await successor.async_mq_send_message("risk.first", b"first")
        assert await asyncio.to_thread(started.wait, 10)
        await successor.async_mq_send_message("risk.second", b"second")
        assert worker.pid is not None
        os.kill(worker.pid, signal.SIGTERM)
        await successor.mq_run()
        await asyncio.wait_for(second_received.wait(), 10)
        assert received == [b"second"]
        assert cleaned.is_set() is False
        assert acknowledged.is_set() is False
        assert worker.is_alive() is True
        release.set()
        await asyncio.to_thread(worker.join, 10)
        assert worker.exitcode == 0
        assert acknowledged.is_set() is True
        assert cleaned.is_set() is True
        await asyncio.sleep(0.2)
        await successor.mq_drain()
        assert received == [b"second"]
        assert successor._queue is not None
        assert await successor._queue.get(fail=False) is None
    finally:
        release.set()
        if worker.is_alive() is True:
            worker.kill()
        await asyncio.to_thread(worker.join, 5)
        await successor.mq_drain()
        await successor.mq_close()
        successor._executor.shutdown()
