"""Unit tests for the oxo root CLI."""

import logging
from collections.abc import Iterator

import pytest
from click import testing as click_testing

from ostorlab.cli import rootcli

OXO_LOGGER = "ostorlab.runtimes.local.runtime"
THIRD_PARTY_LOGGERS = ("sqlalchemy.engine.Engine", "httpx")


@pytest.fixture
def restored_logger_levels() -> Iterator[None]:
    """Restore the level of every registered logger, since the verbosity flags mutate process global state."""
    levels = {
        name: logging.getLogger(name).level
        for name in list(logging.root.manager.loggerDict)
    }
    yield
    for name, level in levels.items():
        logging.getLogger(name).setLevel(level)


def testRootCli_whenVerboseIsEnabled_raisesOxoLoggersVerbosity(
    restored_logger_levels,
) -> None:
    """`-v` must surface oxo's own logs."""
    logging.getLogger(OXO_LOGGER).setLevel(logging.NOTSET)
    runner = click_testing.CliRunner()

    result = runner.invoke(rootcli.rootcli, ["-v", "scan", "--help"])

    assert result.exit_code == 0, result.output
    assert logging.getLogger(OXO_LOGGER).level == logging.INFO


def testRootCli_whenVerboseIsEnabled_keepsThirdPartyLoggersQuiet(
    restored_logger_levels,
) -> None:
    """SQLAlchemy echoes every statement and PRAGMA at INFO, which drowns the oxo logs `-v` is asked for."""
    for name in THIRD_PARTY_LOGGERS:
        logging.getLogger(name).setLevel(logging.NOTSET)
    runner = click_testing.CliRunner()

    result = runner.invoke(rootcli.rootcli, ["-v", "scan", "--help"])

    assert result.exit_code == 0, result.output
    for name in THIRD_PARTY_LOGGERS:
        assert logging.getLogger(name).level == logging.NOTSET


def testRootCli_whenDebugIsEnabled_raisesOxoLoggersVerbosityOnly(
    restored_logger_levels,
) -> None:
    """`-d` goes through the same filtering as `-v`, and must not turn the library internals on either."""
    logging.getLogger(OXO_LOGGER).setLevel(logging.NOTSET)
    for name in THIRD_PARTY_LOGGERS:
        logging.getLogger(name).setLevel(logging.NOTSET)
    runner = click_testing.CliRunner()

    result = runner.invoke(rootcli.rootcli, ["-d", "scan", "--help"])

    assert result.exit_code == 0, result.output
    assert logging.getLogger(OXO_LOGGER).level == logging.DEBUG
    for name in THIRD_PARTY_LOGGERS:
        assert logging.getLogger(name).level == logging.NOTSET
