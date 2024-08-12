from pytest_mock import plugin

from ostorlab.cli import console as cli_console


def testConsoleInfo_whenLoggerSet_shouldLogMessages(
    mocker: plugin.MockerFixture,
) -> None:
    message = "Hello, World!"
    mock_logger = mocker.patch("logging.getLogger")
    console = cli_console.Console(logger=mock_logger)

    console.info(message)

    mock_logger.info.assert_called_once_with(message)


def testConsoleInfo_whenLoggerNotSet_shouldNotLogMessages(
    mocker: plugin.MockerFixture,
) -> None:
    message = "Hello, World!"
    mock_logger = mocker.patch("logging.getLogger")
    console = cli_console.Console()

    console.info(message)

    mock_logger.info.assert_not_called()


def testConsoleError_whenLoggerSet_shouldLogMessages(
    mocker: plugin.MockerFixture,
) -> None:
    error_message = "An error occurred"
    mock_logger = mocker.patch("logging.getLogger")
    console = cli_console.Console(logger=mock_logger)

    console.error(error_message)

    mock_logger.error.assert_called_once_with(error_message)


def testConsoleError_whenLoggerNotSet_shouldNotLogMessages(
    mocker: plugin.MockerFixture,
) -> None:
    error_message = "An error occurred"
    mock_logger = mocker.patch("logging.getLogger")
    console = cli_console.Console()

    console.error(error_message)

    mock_logger.error.assert_not_called()


def testConsoleWarning_whenLoggerSet_shouldLogMessages(
    mocker: plugin.MockerFixture,
) -> None:
    warning_message = "A warning occurred"
    mock_logger = mocker.patch("logging.getLogger")
    console = cli_console.Console(logger=mock_logger)

    console.warning(warning_message)

    mock_logger.warning.assert_called_once_with(warning_message)


def testConsoleWarning_whenLoggerNotSet_shouldNotLogMessages(
    mocker: plugin.MockerFixture,
) -> None:
    warning_message = "A warning occurred"
    mock_logger = mocker.patch("logging.getLogger")
    console = cli_console.Console()

    console.warning(warning_message)

    mock_logger.warning.assert_not_called()
