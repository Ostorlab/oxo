"""Unit tests for the oxo root CLI."""

import logging

from click import testing as click_testing

from ostorlab.cli import rootcli


def testRootCli_whenVerboseIsEnabled_raisesOxoLoggersVerbosity() -> None:
    """`-v` must surface oxo's own logs."""
    oxo_logger = logging.getLogger("ostorlab.runtimes.local.runtime")
    oxo_logger.setLevel(logging.NOTSET)

    runner = click_testing.CliRunner()
    runner.invoke(rootcli.rootcli, ["-v", "scan", "--help"])

    assert oxo_logger.level == logging.INFO


def testRootCli_whenVerboseIsEnabled_keepsThirdPartyLoggersQuiet() -> None:
    """SQLAlchemy echoes every statement and PRAGMA at INFO, which drowns the oxo logs `-v` is asked for."""
    sqlalchemy_logger = logging.getLogger("sqlalchemy.engine.Engine")
    httpx_logger = logging.getLogger("httpx")
    sqlalchemy_logger.setLevel(logging.NOTSET)
    httpx_logger.setLevel(logging.NOTSET)

    runner = click_testing.CliRunner()
    runner.invoke(rootcli.rootcli, ["-v", "scan", "--help"])

    assert sqlalchemy_logger.level == logging.NOTSET
    assert httpx_logger.level == logging.NOTSET
