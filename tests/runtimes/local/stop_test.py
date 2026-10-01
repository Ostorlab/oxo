"""Exercise local stop outcomes through the public runtime and root CLI."""

import docker
import pytest
from click import testing
from pytest_mock import plugin

from ostorlab.cli import docker_requirements_checker
from ostorlab.cli import rootcli
from ostorlab.runtimes.local import runtime
from ostorlab.runtimes.local.models import models


@pytest.fixture
def stop_docker_boundaries(
    offline_docker_client: docker.DockerClient, mocker: plugin.MockerFixture
) -> docker.DockerClient:
    """Isolate Docker checks and operations while keeping SDK collections real."""
    for requirement in (
        "is_docker_installed",
        "is_sys_arch_supported",
        "is_user_permitted",
        "is_docker_working",
        "is_swarm_initialized",
    ):
        mocker.patch.object(docker_requirements_checker, requirement, return_value=True)
    for operation in ("services", "networks", "configs"):
        mocker.patch.object(offline_docker_client.api, operation, return_value=[])
    mocker.patch.object(
        offline_docker_client.api, "volumes", return_value={"Volumes": []}
    )
    mocker.patch.object(
        offline_docker_client.api,
        "inspect_volume",
        side_effect=docker.errors.NotFound("Volume not found"),
    )
    return offline_docker_client


@pytest.mark.parametrize("cleanup_fails", [True, False])
@pytest.mark.parametrize("update_scan_status", [True, False])
def testLocalStop_whenCleanupCompletes_reportsOutcomeAndPreservesCorrectProgress(
    cleanup_fails: bool,
    update_scan_status: bool,
    stop_docker_boundaries: docker.DockerClient,
    mocker: plugin.MockerFixture,
) -> None:
    """A failed SDK operation returns False independently of status updates."""
    scan = models.Scan.create(
        "stop regression", progress=models.ScanProgress.IN_PROGRESS
    )
    if cleanup_fails is True:
        mocker.patch.object(
            stop_docker_boundaries.api,
            "services",
            side_effect=docker.errors.APIError("Service listing failed"),
        )

    result = runtime.LocalRuntime().stop(
        scan_id=scan.id, update_scan_status=update_scan_status
    )

    assert result is (False if cleanup_fails is True else None)
    with models.Database() as session:
        stored_scan = session.get(models.Scan, scan.id)
        assert stored_scan is not None
        expected_progress = (
            models.ScanProgress.STOPPED
            if cleanup_fails is False and update_scan_status is True
            else models.ScanProgress.IN_PROGRESS
        )
        assert stored_scan.progress == expected_progress


@pytest.mark.parametrize("cleanup_fails", [True, False])
def testLocalStopCLI_whenCleanupCompletes_reportsOutcomeAndCorrectProgress(
    cleanup_fails: bool,
    stop_docker_boundaries: docker.DockerClient,
    mocker: plugin.MockerFixture,
) -> None:
    """The root CLI detects a real cleanup failure and leaves the scan running."""
    scan = models.Scan.create(
        "CLI stop regression", progress=models.ScanProgress.IN_PROGRESS
    )
    if cleanup_fails is True:
        mocker.patch.object(
            stop_docker_boundaries.api,
            "services",
            side_effect=docker.errors.APIError("Service listing failed"),
        )

    result = testing.CliRunner().invoke(rootcli.rootcli, ["scan", "stop", str(scan.id)])

    assert result.exit_code == (1 if cleanup_fails is True else 0)
    if cleanup_fails is True:
        assert f"Error: Could not stop scan {scan.id}" in result.output
        assert "stopped successfully" not in result.output
    else:
        assert "Scan stopped successfully" in result.output
    with models.Database() as session:
        stored_scan = session.get(models.Scan, scan.id)
        assert stored_scan is not None
        assert stored_scan.progress == (
            models.ScanProgress.IN_PROGRESS
            if cleanup_fails is True
            else models.ScanProgress.STOPPED
        )


def testLocalStop_whenScanIdMissing_preservesLegacyNone(
    offline_docker_client: docker.DockerClient,
) -> None:
    """Missing scan identifiers remain successful no-ops without Docker I/O."""
    assert runtime.LocalRuntime().stop() is None
