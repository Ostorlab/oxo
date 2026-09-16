from pytest_mock import plugin
from rich import table as rich_table

from ostorlab.cli import console as cli_console
from ostorlab.utils import styles


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


def testConsoleInfo_whenTextHoldsUnbalancedBrackets_shouldNotRaiseMarkupError() -> None:
    """Asset representations may hold regexes or URLs with brackets, rich must not parse them."""
    console = cli_console.Console()

    console.info("Injecting asset: Link(url=https://example.com/[/Pattern])")


def testConsoleErrorWarningSuccess_whenTextHoldsUnbalancedBrackets_shouldNotRaiseMarkupError() -> (
    None
):
    text = "closing tag '[/Pattern]' at position 127"
    console = cli_console.Console()

    console.error(text)
    console.warning(text)
    console.success(text)
    console.status(text)


def testConsoleTable_whenDataHoldsUnbalancedBrackets_shouldNotRaiseMarkupError() -> (
    None
):
    console = cli_console.Console()

    console.table(
        columns={"Target": "target"},
        data=[{"target": "https://example.com/[/Pattern]"}],
        title="Scans",
    )


def testConsoleInfo_whenIsMarkupSet_shouldRenderMarkup(
    mocker: plugin.MockerFixture,
) -> None:
    console = cli_console.Console()
    print_mock = mocker.patch.object(console._console, "print")

    console.info("[bold red]agent[/]", is_markup=True)

    assert print_mock.call_args[0][0] == ":small_blue_diamond: [bold red]agent[/]"


def testConsoleTable_whenCellIsStyledAndDataHoldsBrackets_stylesCellAndEscapesData(
    mocker: plugin.MockerFixture,
) -> None:
    """The styled cells are `Text` renderables, they must survive the escaping of the string cells."""
    console = cli_console.Console()
    add_row_mock = mocker.patch.object(rich_table.Table, "add_row")

    console.table(
        columns={"Risk rating": "risk_rating", "Vulnerable target": "location"},
        data=[
            {
                "risk_rating": styles.style_risk("HIGH"),
                "location": "https://dummy.co/[/Pattern]",
            }
        ],
        title="Scan 1: Found 1 vulnerabilities.",
    )

    risk_cell, location_cell = add_row_mock.call_args[0]
    assert risk_cell.plain == "High"
    assert risk_cell.spans != []
    assert location_cell == "https://dummy.co/\\[/Pattern]"


def testStyleRisk_whenRiskIsUnknown_returnsUnstyledText() -> None:
    styled = styles.style_risk("NOT_A_RATING")

    assert styled.plain == "NOT_A_RATING"
    assert styled.spans == []


def testStyleProgressAndRisk_whenValueIsNone_returnsEmptyText() -> None:
    """Scans listed before they start have no progress nor risk rating."""
    assert styles.style_progress(None).plain == ""
    assert styles.style_risk(None).plain == ""
    assert styles.style_asset(None).plain == ""
