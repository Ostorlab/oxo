"""Test for the system info helper."""
from pytest_mock import plugin

from ostorlab.utils import system


def testGetSystemLoad_always_returnCorrectSystemInfo(
    mocker: plugin.MockerFixture,
) -> None:
    """Test that the system load information is correctly returned."""

    # Prepare
    mocker.patch("psutil.cpu_percent", return_value=[2.2, 1.8])
    mocker.patch(
        "psutil.virtual_memory",
        return_value=mocker.Mock(total=100, available=50, used=50, percent=50),
    )

    # Act
    system_info = system.get_system_info()

    # Assert
    assert system_info is not None
    assert system_info.cpu_load.load == [2.2, 1.8]
    assert system_info.memory_usage.total == 100
    assert system_info.memory_usage.available == 50
    assert system_info.memory_usage.used == 50
    assert system_info.memory_usage.percent == 50


def testGetSystemLoad_whenPsutilNotAvailable_returnCorrectSystemInfo(
    mocker: plugin.MockerFixture,
) -> None:
    """Test when `psutil` is not available, we return None."""
    # Prepare
    mocker.patch("psutil.cpu_percent", side_effect=ImportError())

    # Act
    system_info = system.get_system_info()

    # Assert
    assert system_info is None
