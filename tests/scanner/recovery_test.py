"""Worker recovery through Docker and scanner API boundaries."""

from __future__ import annotations

import json
import typing
from unittest import mock

import docker
import pytest
from pytest_mock import plugin

from ostorlab.apis import scans_active
from ostorlab.scanner import recovery


def _service(scan_id: str = "42", *, running: bool = False) -> mock.MagicMock:
    service = mock.MagicMock()
    service.id = "worker-id"
    service.name = "worker"
    service.attrs = {
        "Spec": {
            "Labels": {"ostorlab.universe": scan_id, "ostorlab.queue_name": "worker"},
            "Mode": {"Replicated": {"Replicas": 1}},
            "TaskTemplate": {
                "RestartPolicy": {"Condition": "any"},
                "ContainerSpec": {"Labels": {"ostorlab.scan_id": scan_id}},
            },
        }
    }
    service.tasks.return_value = [
        {
            "Status": {
                "State": "running" if running else "pending",
                "Err": "insufficient resources",
            }
        }
    ]

    def update(**kwargs: typing.Any) -> None:
        service.attrs["Spec"]["Labels"] = kwargs["labels"]
        service.attrs["Spec"]["TaskTemplate"]["ForceUpdate"] = kwargs["force_update"]

    service.update.side_effect = update
    return service


def _setup(
    mocker: plugin.MockerFixture, *, running: bool = False
) -> tuple[
    recovery.WorkerRecovery,
    mock.MagicMock,
    mock.MagicMock,
    mock.MagicMock,
    mock.MagicMock,
]:
    worker = _service(running=running)
    broker = mock.MagicMock()
    broker.attrs = {"Spec": {"Labels": {"ostorlab.universe": "42", "ostorlab.mq": ""}}}
    broker.tasks.return_value = [
        {"Status": {"State": "running", "ContainerStatus": {"ContainerID": "broker"}}}
    ]
    client = mock.MagicMock(spec=docker.DockerClient)
    client.services.list.return_value = [worker, broker]
    execute = client.containers.get.return_value.exec_run
    execute.return_value = mock.Mock(
        exit_code=0,
        output=b'[{"name":"worker_queue","messages_ready":1,"messages_unacknowledged":0,"consumers":0}]',
    )
    runner = mock.MagicMock()
    runner.execute.return_value = {
        "data": {"scans": {"scans": [{"id": "42"}], "pageInfo": {"numPages": 1}}}
    }
    mocker.patch("ostorlab.scanner.recovery.time.monotonic", return_value=1000.0)
    mocker.patch("ostorlab.scanner.recovery.time.time", return_value=1000.0)
    return recovery.WorkerRecovery(client), worker, broker, runner, execute


def _advance(mocker: plugin.MockerFixture, seconds: float) -> None:
    mocker.patch("ostorlab.scanner.recovery.time.monotonic", return_value=seconds)
    mocker.patch("ostorlab.scanner.recovery.time.time", return_value=seconds)


def testRecovery_whenWorkerStalls_restartsOnlyWorkerAfterGrace(
    mocker: plugin.MockerFixture,
) -> None:
    reconciler, worker, broker, runner, execute = _setup(mocker)
    reconciler.reconcile(runner)
    worker.update.assert_not_called()
    _advance(mocker, 1121)
    reconciler.reconcile(runner)
    assert worker.attrs["Spec"]["TaskTemplate"]["ForceUpdate"] == 1
    assert worker.attrs["Spec"]["Labels"]["ostorlab.recovery.attempts"] == "1"
    broker.update.assert_not_called()
    broker.remove.assert_not_called()
    assert execute.call_args.args[0] == [
        "rabbitmqctl",
        "list_queues",
        "--formatter=json",
        "--timeout",
        "10",
        "name",
        "messages_ready",
        "messages_unacknowledged",
        "consumers",
    ]


def testRecovery_whenAttemptsExhausted_reportsErrorAndRetainsBroker(
    mocker: plugin.MockerFixture,
) -> None:
    reconciler, worker, broker, runner, _ = _setup(mocker)
    reconciler.reconcile(runner)
    for seconds in (1121, 1182, 1242, 1363):
        _advance(mocker, seconds)
        reconciler.reconcile(runner)
    assert worker.update.call_count == 2
    updates = [
        json.loads(call.kwargs["request"].data["variables"])
        for call in runner.execute.call_args_list
        if not isinstance(call.kwargs["request"], scans_active.ScansActiveAPIRequest)
    ]
    assert updates == [{"scanId": 42, "progress": "error", "scannerId": None}]
    broker.remove.assert_not_called()


@pytest.mark.parametrize(
    "change", ["inactive", "zero", "once", "shared", "healthy", "partial"]
)
def testRecovery_whenWorkerIneligible_doesNotRestart(
    mocker: plugin.MockerFixture, change: str
) -> None:
    reconciler, worker, _, runner, execute = _setup(mocker)
    if change == "inactive":
        runner.execute.return_value["data"]["scans"]["scans"] = []
    elif change == "zero":
        worker.attrs["Spec"]["Mode"]["Replicated"]["Replicas"] = 0
    elif change == "once":
        worker.attrs["Spec"]["TaskTemplate"]["RestartPolicy"]["Condition"] = "none"
    elif change == "shared":
        worker.attrs["Spec"]["TaskTemplate"]["ContainerSpec"]["Labels"][
            "ostorlab.scan_id"
        ] = "other"
    else:
        worker.tasks.return_value = [{"Status": {"State": "running"}}]
        execute.return_value.output = b'[{"name":"worker_queue","messages_ready":99,"messages_unacknowledged":1,"consumers":1}]'
        if change == "partial":
            worker.attrs["Spec"]["Mode"]["Replicated"]["Replicas"] = 2
    reconciler.reconcile(runner)
    _advance(mocker, 1500)
    reconciler.reconcile(runner)
    worker.update.assert_not_called()


def testRecovery_whenFailedQueueContainsMessage_reportsActionableError(
    mocker: plugin.MockerFixture, caplog: pytest.LogCaptureFixture
) -> None:
    reconciler, worker, broker, runner, execute = _setup(mocker, running=True)
    execute.return_value.output = b'[{"name":"worker_queue.failed","messages_ready":1,"messages_unacknowledged":0,"consumers":0}]'
    reconciler.reconcile(runner)
    assert "worker_queue.failed" in caplog.text
    assert (
        json.loads(runner.execute.call_args.kwargs["request"].data["variables"])[
            "progress"
        ]
        == "error"
    )
    worker.update.assert_not_called()
    broker.remove.assert_not_called()


def testRecovery_whenScannerRestarts_preservesBoundedAttempts(
    mocker: plugin.MockerFixture,
) -> None:
    reconciler, worker, _, runner, _ = _setup(mocker)
    worker.attrs["Spec"]["Labels"].update(
        {"ostorlab.recovery.attempts": "2", "ostorlab.recovery.last_attempt": "900"}
    )
    reconciler.reconcile(runner)
    _advance(mocker, 1121)
    reconciler.reconcile(runner)
    worker.update.assert_not_called()
    assert (
        json.loads(runner.execute.call_args.kwargs["request"].data["variables"])[
            "progress"
        ]
        == "error"
    )


def testRecovery_whenPausedBeforeAction_doesNotRestart(
    mocker: plugin.MockerFixture,
) -> None:
    reconciler, worker, _, runner, _ = _setup(mocker)
    reconciler.reconcile(runner)
    active = runner.execute.return_value
    inactive = {"data": {"scans": {"scans": [], "pageInfo": {"numPages": 1}}}}
    runner.execute.side_effect = [active, inactive]
    _advance(mocker, 1121)
    reconciler.reconcile(runner)
    worker.update.assert_not_called()


def testActiveScans_whenPaginated_returnsAllIds(mocker: plugin.MockerFixture) -> None:
    runner = mocker.MagicMock()
    runner.execute.side_effect = [
        {
            "data": {
                "scans": {"scans": [{"id": str(scan_id)}], "pageInfo": {"numPages": 2}}
            }
        }
        for scan_id in (42, 43)
    ]
    assert recovery.active_scan_ids(runner) == {"42", "43"}
    assert [
        json.loads(call.kwargs["request"].data["variables"])["page"]
        for call in runner.execute.call_args_list
    ] == [1, 2]
    assert json.loads(runner.execute.call_args.kwargs["request"].data["variables"])[
        "progresses"
    ] == ["in_progress"]


@pytest.mark.parametrize(
    "response",
    [
        {},
        {"errors": [{"message": "denied"}]},
        {"data": {"scans": {"scans": [], "pageInfo": {"numPages": 2}}}},
    ],
)
def testActiveScans_whenIncomplete_failsClosed(
    mocker: plugin.MockerFixture, response: dict[str, typing.Any]
) -> None:
    runner = mocker.MagicMock()
    runner.execute.return_value = response
    assert recovery.active_scan_ids(runner) is None


def testRecovery_whenWithinPollingInterval_doesNotQueryAgain(
    mocker: plugin.MockerFixture,
) -> None:
    reconciler, worker, _, runner, execute = _setup(mocker)
    reconciler.reconcile(runner)
    _advance(mocker, 1005)
    reconciler.reconcile(runner)
    assert runner.execute.call_count == 1
    assert execute.call_count == 1
    worker.update.assert_not_called()


def testRecovery_whenWithinCooldown_doesNotRepeatRestart(
    mocker: plugin.MockerFixture,
) -> None:
    reconciler, worker, _, runner, _ = _setup(mocker)
    reconciler.reconcile(runner)
    _advance(mocker, 1121)
    reconciler.reconcile(runner)
    _advance(mocker, 1182)
    reconciler.reconcile(runner)
    assert worker.update.call_count == 1


@pytest.mark.parametrize(
    "change", ["deleted", "scaled_zero", "paused", "api_error", "broker_error"]
)
def testRecovery_whenActionBecomesUnsafe_retainsAllServices(
    mocker: plugin.MockerFixture, change: str
) -> None:
    reconciler, worker, broker, runner, execute = _setup(mocker)
    reconciler.reconcile(runner)
    if change == "deleted":
        worker.reload.side_effect = docker.errors.NotFound("deleted")
    elif change == "scaled_zero":

        def reload_worker() -> None:
            worker.attrs["Spec"]["Mode"]["Replicated"]["Replicas"] = 0

        worker.reload.side_effect = reload_worker
    elif change == "paused":
        runner.execute.return_value["data"]["scans"]["scans"] = []
    elif change == "api_error":
        runner.execute.return_value = {"errors": [{"message": "unavailable"}]}
    else:
        execute.return_value.exit_code = 70
    _advance(mocker, 1121)
    reconciler.reconcile(runner)
    worker.update.assert_not_called()
    worker.remove.assert_not_called()
    broker.update.assert_not_called()
    broker.remove.assert_not_called()


def testActiveScans_whenFinalPageMissing_failsClosed(
    mocker: plugin.MockerFixture,
) -> None:
    runner = mocker.MagicMock()
    runner.execute.side_effect = [
        {"data": {"scans": {"scans": [{"id": "42"}], "pageInfo": {"numPages": 2}}}},
        {"data": {"scans": {"scans": [], "pageInfo": {"numPages": 2}}}},
    ]
    assert recovery.active_scan_ids(runner) is None


def testRecovery_whenWorkerRestartsOnFailure_recoversStall(
    mocker: plugin.MockerFixture,
) -> None:
    reconciler, worker, _, runner, _ = _setup(mocker)
    worker.attrs["Spec"]["TaskTemplate"]["RestartPolicy"]["Condition"] = "on-failure"
    reconciler.reconcile(runner)
    _advance(mocker, 1121)
    reconciler.reconcile(runner)
    assert worker.attrs["Spec"]["TaskTemplate"]["ForceUpdate"] == 1


def testRecovery_whenErrorUpdateHasNullData_logsUnconfirmedState(
    mocker: plugin.MockerFixture, caplog: pytest.LogCaptureFixture
) -> None:
    reconciler, worker, broker, runner, execute = _setup(mocker)
    active = runner.execute.return_value
    runner.execute.side_effect = [active, active, {"data": None}]
    execute.return_value.output = b'[{"name":"worker_queue.failed","messages_ready":1,"messages_unacknowledged":0,"consumers":0}]'
    reconciler.reconcile(runner)
    assert "did not confirm error state" in caplog.text
    worker.update.assert_not_called()
    broker.remove.assert_not_called()
