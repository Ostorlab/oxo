"""Unit tests for install_progress.py module."""
from ostorlab.cli.agent.install import install_progress


def testAgentInstallProgress_whenLogsGeneratorHasLogs_displaysProgress() -> None:
    """Test the agent install progress when the logs generator has logs."""
    progress = install_progress.AgentInstallProgress()
    logs_generator = iter(
        [
            {
                "id": "1",
                "status": ["Downloading"],
                "progressDetail": {"total": 100, "current": 50},
            },
            {"id": "1", "status": ["Download complete"]},
            {
                "id": "2",
                "status": ["Extracting"],
                "progressDetail": {"total": 100, "current": 50},
            },
        ]
    )

    progress.display(logs_generator)

    assert progress is not None


def testAgentInstallProgress_whenTotalIsMissing_doesNotCrash() -> None:
    """Test the agent install progress when the total attr is missing."""
    progress = install_progress.AgentInstallProgress()
    logs_generator = iter(
        [
            {
                "id": "1",
                "status": ["Downloading"],
                "progressDetail": {"current": 50},
            },
            {"id": "1", "status": ["Download complete"]},
            {
                "id": "2",
                "status": ["Extracting"],
                "progressDetail": {"current": 50},
            },
        ]
    )

    progress.display(logs_generator)

    assert progress is not None


def testAgentInstallProgress_whenCurrentIsMissing_doesNotCrash() -> None:
    """Test the agent install progress when the current attr is missing."""
    progress = install_progress.AgentInstallProgress()
    logs_generator = iter(
        [
            {
                "id": "1",
                "status": ["Downloading"],
                "progressDetail": {"total": 100},
            },
            {"id": "1", "status": ["Download complete"]},
            {
                "id": "2",
                "status": ["Extracting"],
                "progressDetail": {"total": 100},
            },
        ]
    )

    progress.display(logs_generator)

    assert progress is not None
