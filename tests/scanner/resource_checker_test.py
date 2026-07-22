"""Tests for scanner host resource checks."""

import logging
from types import SimpleNamespace

from pytest_mock import plugin

from ostorlab.scanner import resource_checker
from ostorlab.scanner import scanner_conf


def testCanRunScan_whenHostHasRequiredResources_returnsTrue(
    mocker: plugin.MockerFixture,
) -> None:
    mocker.patch("psutil.cpu_count", return_value=8)
    mocker.patch(
        "psutil.virtual_memory", return_value=SimpleNamespace(available=20_000)
    )
    mocker.patch("psutil.disk_usage", return_value=SimpleNamespace(free=30_000))
    requirements = {
        "agentgroup/ostorlab/test": scanner_conf.ScanResourceRequirements(
            cpu_count=4, memory=10_000, disk=20_000
        )
    }

    assert (
        resource_checker.can_run_scan("agentgroup/ostorlab/test", requirements) is True
    )


def testCanRunScan_whenHostDoesNotHaveRequiredResources_returnsFalse(
    mocker: plugin.MockerFixture,
) -> None:
    mocker.patch("psutil.cpu_count", return_value=2)
    mocker.patch("psutil.virtual_memory", return_value=SimpleNamespace(available=5_000))
    mocker.patch("psutil.disk_usage", return_value=SimpleNamespace(free=5_000))
    requirements = {
        "agentgroup/ostorlab/test": scanner_conf.ScanResourceRequirements(
            cpu_count=4, memory=10_000, disk=20_000
        )
    }

    assert (
        resource_checker.can_run_scan("agentgroup/ostorlab/test", requirements) is False
    )


def testCanRunScan_whenRequirementsAreMissing_returnsFalse() -> None:
    assert resource_checker.can_run_scan("agentgroup/ostorlab/test", {}) is False


def testCanRunScan_whenFullKeyMissing_usesShortKey(
    mocker: plugin.MockerFixture,
) -> None:
    mocker.patch("psutil.cpu_count", return_value=8)
    mocker.patch(
        "psutil.virtual_memory", return_value=SimpleNamespace(available=20_000)
    )
    mocker.patch("psutil.disk_usage", return_value=SimpleNamespace(free=30_000))
    requirements = {
        "test": scanner_conf.ScanResourceRequirements(
            cpu_count=4, memory=10_000, disk=20_000
        )
    }

    assert (
        resource_checker.can_run_scan("agentgroup/ostorlab/test", requirements) is True
    )


def testCanRunScan_whenScanKeyMissing_usesDefault(
    mocker: plugin.MockerFixture,
) -> None:
    mocker.patch("psutil.cpu_count", return_value=8)
    mocker.patch(
        "psutil.virtual_memory", return_value=SimpleNamespace(available=20_000)
    )
    mocker.patch("psutil.disk_usage", return_value=SimpleNamespace(free=30_000))
    requirements = {
        "default": scanner_conf.ScanResourceRequirements(
            cpu_count=4, memory=10_000, disk=20_000
        )
    }

    assert (
        resource_checker.can_run_scan("agentgroup/ostorlab/test", requirements) is True
    )


def testCanRunScan_whenResourceCollectionFails_returnsFalse(
    mocker: plugin.MockerFixture,
    caplog,
) -> None:
    mocker.patch("psutil.cpu_count", side_effect=OSError("host unavailable"))
    requirements = {
        "agentgroup/ostorlab/test": scanner_conf.ScanResourceRequirements(
            cpu_count=4, memory=10_000, disk=20_000
        )
    }

    with caplog.at_level(logging.WARNING):
        can_run = resource_checker.can_run_scan(
            "agentgroup/ostorlab/test", requirements
        )

    assert can_run is False
    assert "Unable to determine host resources" in caplog.text


def testCanRunScan_whenDiskPathProvided_checksConfiguredPath(
    mocker: plugin.MockerFixture,
) -> None:
    mocker.patch("psutil.cpu_count", return_value=8)
    mocker.patch(
        "psutil.virtual_memory", return_value=SimpleNamespace(available=20_000)
    )
    disk_usage = mocker.patch(
        "psutil.disk_usage", return_value=SimpleNamespace(free=30_000)
    )
    requirements = {
        "agentgroup/ostorlab/test": scanner_conf.ScanResourceRequirements(
            cpu_count=4, memory=10_000, disk=20_000
        )
    }

    can_run = resource_checker.can_run_scan(
        "agentgroup/ostorlab/test",
        requirements,
        disk_path="/scan-data",
    )

    assert can_run is True
    disk_usage.assert_called_once_with("/scan-data")
