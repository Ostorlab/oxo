"""Tests for scan run command."""

import multiprocessing
import os
import pathlib
import re
from collections.abc import Callable
from typing import Optional

import pytest_httpx
from click.testing import CliRunner
from pytest_mock import plugin

from ostorlab.cli import rootcli
from ostorlab.cli.ci_scan import run

TEST_FILE_PATH = str(pathlib.Path(__file__).parent / "test_file")


def _strip_ansi(text: str) -> str:
    """Strip ANSI escape sequences from CLI output for stable assertions."""
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def testRunScanCLI_WhenApiKeyIsMissing_ShowError(mocker: plugin.MockerFixture) -> None:
    """Test ostorlab ci_scan with no api key. it should exit with error exit_code = 2."""
    mocker.patch(
        "ostorlab.apis.runners.authenticated_runner.AuthenticatedAPIRunner.execute",
        return_value=True,
    )
    runner = CliRunner()
    result = runner.invoke(
        rootcli.rootcli,
        [
            "ci-scan",
            "run",
            "--scan-profile=fast_scan",
            "--title=scan1",
            "android-aab",
            TEST_FILE_PATH,
        ],
    )

    assert isinstance(result.exception, BaseException)
    assert "API key not not provided." in _strip_ansi(result.output)


def testRunScanCLI_whenBreakOnRiskRatingIsNotSet_ReturnsIdScan(
    mocker: plugin.MockerFixture,
) -> None:
    """Test ostorlab ci_scan with no break_on_risk_rating. it should create the scan and returns its id."""
    scan_create_dict = {"data": {"createMobileScan": {"scan": {"id": "1"}}}}

    mocker.patch(
        "ostorlab.apis.runners.authenticated_runner.AuthenticatedAPIRunner.execute",
        return_value=scan_create_dict,
    )
    runner = CliRunner()
    result = runner.invoke(
        rootcli.rootcli,
        [
            "--api-key=12",
            "ci-scan",
            "run",
            "--scan-profile=full_scan",
            "--title=scan1",
            "android-apk",
            TEST_FILE_PATH,
        ],
    )

    assert "Scan created with id 1." in _strip_ansi(result.output)


def testRunScanCLI_whenBreakOnRiskRatingIsSetWithInvalidValue_ShowError(
    mocker: plugin.MockerFixture,
) -> None:
    """Test ostorlab ci_scan with invalid break_on_risk_rating. it should exit with error exit_code = 2."""
    scan_create_dict = {"data": {"createMobileScan": {"scan": {"id": "1"}}}}
    mocker.patch(
        "ostorlab.apis.runners.authenticated_runner.AuthenticatedAPIRunner.execute",
        return_value=scan_create_dict,
    )
    runner = CliRunner()
    result = runner.invoke(
        rootcli.rootcli,
        [
            "--api-key=12",
            "ci-scan",
            "run",
            "--scan-profile=full_scan",
            "--break-on-risk-rating=toto",
            "--title=scan1",
            "ios-ipa",
            TEST_FILE_PATH,
        ],
    )

    assert "Scan created with id 1." in _strip_ansi(result.output)
    assert "Incorrect risk rating value toto." in _strip_ansi(result.output)
    assert isinstance(result.exception, BaseException)


def testRunScanCLI_whenBreakOnRiskRatingIsSetAndScanTimeout_WaitScan(
    mocker: plugin.MockerFixture,
) -> None:
    """Test ostorlab ci_scan with invalid break_on_risk_rating. it should exit with error exit_code = 2."""
    scan_create_dict = {"data": {"createMobileScan": {"scan": {"id": "1"}}}}

    scan_info_dict = {
        "data": {
            "scan": {
                "progress": "not_started",
                "riskRating": "info",
            }
        }
    }
    mocker.patch(
        "ostorlab.apis.runners.authenticated_runner.AuthenticatedAPIRunner.execute",
        side_effect=[scan_create_dict, scan_info_dict],
    )

    class MockProcess:
        """Mock process to deterministically trigger timeout handling in tests."""

        def __init__(
            self,
            target: Optional[Callable[..., object]] = None,
            args: tuple[object, ...] = (),
        ) -> None:
            self._alive = True

        def start(self) -> None:
            return None

        def join(self, timeout: Optional[float] = None) -> None:
            return None

        def is_alive(self) -> bool:
            return self._alive

        def kill(self) -> None:
            self._alive = False

    mocker.patch.object(multiprocessing, "Process", MockProcess)
    mocker.patch.object(run.run, "MINUTE", 1)
    mocker.patch.object(run.run, "SLEEP_CHECKS", 5)

    runner = CliRunner()
    result = runner.invoke(
        rootcli.rootcli,
        [
            "--api-key=12",
            "ci-scan",
            "run",
            "--scan-profile=full_scan",
            "--break-on-risk-rating=medium",
            "--max-wait-minutes=1",
            "--title=scan1",
            "android-apk",
            TEST_FILE_PATH,
        ],
    )

    output = _strip_ansi(_strip_ansi(result.output))
    assert "Scan created with id 1." in output
    assert "The scan is still running." in output
    assert isinstance(result.exception, BaseException)


def testRunScanCLI_whenBreakOnRiskRatingIsSetAndScanDone_ScanDone(
    mocker: plugin.MockerFixture,
) -> None:
    """Test ostorlab ci_scan with invalid break_on_risk_rating. it should exit with error exit_code = 2."""
    scan_create_dict = {"data": {"createMobileScan": {"scan": {"id": "1"}}}}

    scan_info_dict = {
        "data": {
            "scan": {
                "progress": "done",
                "riskRating": "info",
            }
        }
    }
    mocker.patch(
        "ostorlab.apis.runners.authenticated_runner.AuthenticatedAPIRunner.execute",
        side_effect=[scan_create_dict, scan_info_dict, scan_info_dict],
    )
    mocker.patch.object(run.run, "SLEEP_CHECKS", 1)

    runner = CliRunner()
    result = runner.invoke(
        rootcli.rootcli,
        [
            "--api-key=12",
            "ci-scan",
            "run",
            "--scan-profile=full_scan",
            "--break-on-risk-rating=low",
            "--max-wait-minutes=10",
            "--title=scan1",
            "android-apk",
            TEST_FILE_PATH,
        ],
    )

    assert "Scan created with id 1." in _strip_ansi(result.output)
    assert "Scan done with risk rating info." in _strip_ansi(result.output)


def testRunScanCLI_whenBreakOnRiskRatingIsSetAndScanDoneHigherRisk_ShowError(
    mocker: plugin.MockerFixture,
) -> None:
    """Test ostorlab ci_scan with invalid break_on_risk_rating. it should exit with error exit_code = 2."""
    scan_create_dict = {"data": {"createMobileScan": {"scan": {"id": "1"}}}}

    scan_info_dict = {
        "data": {
            "scan": {
                "progress": "done",
                "riskRating": "high",
            }
        }
    }
    mocker.patch(
        "ostorlab.apis.runners.authenticated_runner.AuthenticatedAPIRunner.execute",
        side_effect=[scan_create_dict, scan_info_dict, scan_info_dict],
    )
    mocker.patch.object(run.run, "SLEEP_CHECKS", 1)

    runner = CliRunner()
    result = runner.invoke(
        rootcli.rootcli,
        [
            "--api-key=12",
            "ci-scan",
            "run",
            "--scan-profile=full_scan",
            "--break-on-risk-rating=medium",
            "--max-wait-minutes=10",
            "--title=scan1",
            "ios-ipa",
            TEST_FILE_PATH,
        ],
    )

    assert "Scan created with id 1." in _strip_ansi(result.output)
    assert "The scan risk rating is high." in _strip_ansi(result.output)
    assert isinstance(result.exception, BaseException)


def testRunScanCLI_whithLogLfavorGithub_PrintExpctedOutput(
    mocker: plugin.MockerFixture,
) -> None:
    """Test ostorlab ci_scan with invalid break_on_risk_rating. it should exit with error exit_code = 2."""
    scan_create_dict = {"data": {"createMobileScan": {"scan": {"id": "1"}}}}

    scan_info_dict = {
        "data": {
            "scan": {
                "progress": "done",
                "riskRating": "high",
            }
        }
    }
    mocker.patch(
        "ostorlab.apis.runners.authenticated_runner.AuthenticatedAPIRunner.execute",
        side_effect=[scan_create_dict, scan_info_dict, scan_info_dict],
    )
    mocker.patch.object(run.run, "SLEEP_CHECKS", 1)

    runner = CliRunner()
    result = runner.invoke(
        rootcli.rootcli,
        [
            "--api-key=12",
            "ci-scan",
            "run",
            "--scan-profile=full_scan",
            "--break-on-risk-rating=medium",
            "--max-wait-minutes=10",
            "--title=scan1",
            "--log-flavor=github",
            "ios-ipa",
            TEST_FILE_PATH,
        ],
    )

    assert "Scan created with id 1." in _strip_ansi(result.output)
    assert "::set-output name=scan_id::1" in _strip_ansi(result.output)
    assert "The scan risk rating is high." in _strip_ansi(result.output)
    assert isinstance(result.exception, BaseException)


def testRunScanCLI_withTestCredentials_callsCreateTestCredentials(
    mocker: plugin.MockerFixture,
) -> None:
    """Test ostorlab ci_scan with invalid break_on_risk_rating. it should exit with error exit_code = 2."""

    test_credentials_create_dict = {
        "data": {"createTestCredentials": {"testCredentials": {"id": "456"}}}
    }

    scan_create_dict = {"data": {"createMobileScan": {"scan": {"id": "1"}}}}
    scan_info_dict = {
        "data": {
            "scan": {
                "progress": "done",
                "riskRating": "high",
            }
        }
    }
    mocker.patch(
        "ostorlab.apis.runners.authenticated_runner.AuthenticatedAPIRunner.execute",
        side_effect=[
            test_credentials_create_dict,
            test_credentials_create_dict,
            scan_create_dict,
            scan_info_dict,
            scan_info_dict,
        ],
    )
    mocker.patch.object(run.run, "SLEEP_CHECKS", 1)

    runner = CliRunner()
    result = runner.invoke(
        rootcli.rootcli,
        [
            "--api-key=12",
            "ci-scan",
            "run",
            "--test-credentials-login=test",
            "--test-credentials-password=pass",
            "--test-credentials-name=op",
            "--test-credentials-value=val1",
            "--scan-profile=full_scan",
            "--title=scan1",
            "--log-flavor=github",
            "ios-ipa",
            TEST_FILE_PATH,
        ],
    )
    assert "Created test credentials" in _strip_ansi(result.output)
    assert "Scan created with id 1." in _strip_ansi(result.output)
    assert "password='pass'" not in _strip_ansi(result.output)
    assert "************" in _strip_ansi(result.output)


def testRunScanCLI_withNewTestCredentials_callsCreateTestCredentials(
    mocker: plugin.MockerFixture,
) -> None:
    """Test ostorlab ci_scan with new 2FA/TOTP test credentials."""

    test_credentials_create_dict = {
        "data": {"createTestCredentials": {"testCredentials": {"id": "456"}}}
    }

    scan_create_dict = {"data": {"createMobileScan": {"scan": {"id": "1"}}}}
    scan_info_dict = {
        "data": {
            "scan": {
                "progress": "done",
                "riskRating": "high",
            }
        }
    }
    mocker.patch(
        "ostorlab.apis.runners.authenticated_runner.AuthenticatedAPIRunner.execute",
        side_effect=[
            test_credentials_create_dict,
            test_credentials_create_dict,
            test_credentials_create_dict,
            scan_create_dict,
            scan_info_dict,
            scan_info_dict,
        ],
    )
    mocker.patch.object(run.run, "SLEEP_CHECKS", 1)

    runner = CliRunner()
    result = runner.invoke(
        rootcli.rootcli,
        [
            "--api-key=12",
            "ci-scan",
            "run",
            "--email-2fa-sender-email-address=sender@ex.com",
            "--email-2fa-email-address=user@ex.com",
            "--email-2fa-password=pass",
            "--sms-2fa-sender=+123",
            "--totp-2fa-seed=123456",
            "--scan-profile=full_scan",
            "--title=scan1",
            "ios-ipa",
            TEST_FILE_PATH,
        ],
    )

    assert result.exit_code == 0
    assert "Created test credentials" in _strip_ansi(result.output)
    assert "Scan created with id 1." in _strip_ansi(result.output)


def testRunScanCLI_withInvalidEmail2FAArgs_exitsWithError(
    mocker: plugin.MockerFixture,
) -> None:
    """Test ostorlab ci_scan with invalid email 2FA args."""
    runner = CliRunner()
    # Provide only 2/3 required arguments
    result = runner.invoke(
        rootcli.rootcli,
        [
            "--api-key=12",
            "ci-scan",
            "run",
            "--email-2fa-sender-email-address=sender@ex.com",
            "--email-2fa-email-address=user@ex.com",
            "--scan-profile=full_scan",
            "ios-ipa",
            TEST_FILE_PATH,
        ],
    )
    assert result.exit_code == 2
    assert "Email 2FA credentials are not matching count." in _strip_ansi(result.output)


def testRunScanCLI_withLogLfavorCircleCi_setExpectedEnvVariable(
    mocker: plugin.MockerFixture,
) -> None:
    """Test ostorlab ci_scan with LogFlavor circleci."""
    scan_create_dict = {"data": {"createMobileScan": {"scan": {"id": "1"}}}}

    scan_info_dict = {
        "data": {
            "scan": {
                "progress": "done",
                "riskRating": "high",
            }
        }
    }
    mocker.patch(
        "ostorlab.apis.runners.authenticated_runner.AuthenticatedAPIRunner.execute",
        side_effect=[scan_create_dict, scan_info_dict, scan_info_dict],
    )
    mocker.patch.object(run.run, "SLEEP_CHECKS", 1)

    runner = CliRunner()
    runner.invoke(
        rootcli.rootcli,
        [
            "--api-key=12",
            "ci-scan",
            "run",
            "--scan-profile=full_scan",
            "--break-on-risk-rating=medium",
            "--max-wait-minutes=10",
            "--title=scan1",
            "--log-flavor=circleci",
            "ios-ipa",
            TEST_FILE_PATH,
        ],
    )

    assert "SCAN_ID" in os.environ
    assert os.environ.get("SCAN_ID") == "1"


def testRunScanCLI_withsboms_callApi(
    mocker: plugin.MockerFixture, httpx_mock: pytest_httpx.HTTPXMock
) -> None:
    """Test ostorlab ci_scan with LogFlavor circleci."""
    scan_create_dict = {"data": {"createMobileScan": {"scan": {"id": "1"}}}}

    scan_info_dict = {
        "data": {
            "scan": {
                "progress": "done",
                "riskRating": "high",
            }
        }
    }
    api_caller_mock = mocker.patch(
        "ostorlab.apis.runners.authenticated_runner.AuthenticatedAPIRunner.execute",
        side_effect=[scan_create_dict, scan_info_dict, scan_info_dict],
    )
    mocker.patch.object(run.run, "SLEEP_CHECKS", 1)

    runner = CliRunner()
    runner.invoke(
        rootcli.rootcli,
        [
            "--api-key=12",
            "ci-scan",
            "run",
            "--scan-profile=full_scan",
            "--break-on-risk-rating=medium",
            "--max-wait-minutes=10",
            "--title=scan1",
            "--sbom",
            TEST_FILE_PATH,
            "--sbom",
            TEST_FILE_PATH,
            "android-apk",
            TEST_FILE_PATH,
        ],
    )

    assert api_caller_mock.call_count == 2


def testRunWebScanCLI_withsboms_callApi(
    mocker: plugin.MockerFixture, httpx_mock: pytest_httpx.HTTPXMock
) -> None:
    """Test ostorlab ci_scan with sbom circleci."""
    scan_create_dict = {"data": {"createWebScan": {"scan": {"id": "1"}}}}

    scan_info_dict = {
        "data": {
            "scan": {
                "progress": "done",
                "riskRating": "high",
            }
        }
    }
    api_caller_mock = mocker.patch(
        "ostorlab.apis.runners.authenticated_runner.AuthenticatedAPIRunner.execute",
        side_effect=[scan_create_dict, scan_info_dict, scan_info_dict],
    )
    mocker.patch.object(run.run, "SLEEP_CHECKS", 1)

    runner = CliRunner()

    runner.invoke(
        rootcli.rootcli,
        [
            "--api-key=12",
            "ci-scan",
            "run",
            "--scan-profile=full_web_scan",
            "--break-on-risk-rating=medium",
            "--max-wait-minutes=10",
            "--title=scan1",
            "link",
            "--url",
            "https://test1.com",
        ],
    )

    assert api_caller_mock.call_count == 2
    assert hasattr(api_caller_mock.call_args_list[0].args[0], "_scan_source") is False


def testRunWebScanCLI_withScopeUrlsRegexes_passesRegexesToApi(
    mocker: plugin.MockerFixture,
) -> None:
    """Test ostorlab ci_scan with LogFlavor circleci."""
    scan_create_dict = {"data": {"createMobileScan": {"scan": {"id": "1"}}}}

    scan_info_dict = {
        "data": {
            "scan": {
                "progress": "done",
                "riskRating": "high",
            }
        }
    }
    api_caller_mock = mocker.patch(
        "ostorlab.apis.runners.authenticated_runner.AuthenticatedAPIRunner.execute",
        side_effect=[scan_create_dict, scan_info_dict, scan_info_dict],
    )
    mocker.patch.object(run.run, "SLEEP_CHECKS", 1)

    runner = CliRunner()
    runner.invoke(
        rootcli.rootcli,
        [
            "--api-key=12",
            "ci-scan",
            "run",
            "--scan-profile=full_scan",
            "--break-on-risk-rating=medium",
            "--max-wait-minutes=10",
            "--scope-urls-regexes=^https://example.com/.*$",
            "--scope-urls-regexes=^https://test.com/.*$",
            "--title=scan1",
            "--sbom",
            TEST_FILE_PATH,
            "--sbom",
            TEST_FILE_PATH,
            "android-apk",
            TEST_FILE_PATH,
        ],
    )

    assert api_caller_mock.call_count == 2
    assert api_caller_mock.call_args_list[0].args[0]._scope_urls_regexes == [
        "^https://example.com/.*$",
        "^https://test.com/.*$",
    ]


def testRunScanCLI_withSourceGithub_callApi(mocker: plugin.MockerFixture) -> None:
    """Test ostorlab ci_scan with invalid break_on_risk_rating. it should exit with error exit_code = 2."""
    scan_create_dict = {"data": {"createMobileScan": {"scan": {"id": "1"}}}}

    scan_info_dict = {
        "data": {
            "scan": {
                "progress": "done",
                "riskRating": "high",
            }
        }
    }

    api_caller_mock = mocker.patch(
        "ostorlab.apis.runners.authenticated_runner.AuthenticatedAPIRunner.execute",
        side_effect=[scan_create_dict, scan_info_dict, scan_info_dict],
    )
    mocker.patch.object(run.run, "SLEEP_CHECKS", 1)

    runner = CliRunner()
    runner.invoke(
        rootcli.rootcli,
        [
            "--api-key=12",
            "ci-scan",
            "run",
            "--scan-profile=full_scan",
            "--break-on-risk-rating=medium",
            "--max-wait-minutes=10",
            "--title=scan1",
            "--log-flavor=github",
            "--source=github",
            "--repository=org/repo",
            "--pr-number=123456",
            "--branch=main",
            "ios-ipa",
            TEST_FILE_PATH,
        ],
    )

    assert api_caller_mock.call_count == 2
    assert api_caller_mock.call_args_list[0].args[0]._scan_source.source == "github"
    assert (
        api_caller_mock.call_args_list[0].args[0]._scan_source.repository == "org/repo"
    )
    assert api_caller_mock.call_args_list[0].args[0]._scan_source.pr_number == "123456"
    assert api_caller_mock.call_args_list[0].args[0]._scan_source.branch == "main"


def testRunScanCLI_withUIPromptIds_usesExistingPrompts(
    mocker: plugin.MockerFixture,
) -> None:
    """Test ostorlab ci_scan with UI prompt IDs uses existing prompts directly."""
    scan_create_dict = {"data": {"createMobileScan": {"scan": {"id": "1"}}}}
    api_caller_mock = mocker.patch(
        "ostorlab.apis.runners.authenticated_runner.AuthenticatedAPIRunner.execute",
        return_value=scan_create_dict,
    )
    mocker.patch.object(run.run, "SLEEP_CHECKS", 1)
    runner = CliRunner()

    result = runner.invoke(
        rootcli.rootcli,
        [
            "--api-key=12",
            "ci-scan",
            "run",
            "--scan-profile=full_scan",
            "--title=scan1",
            "--ui-prompt-id=123",
            "--ui-prompt-id=456",
            "android-apk",
            TEST_FILE_PATH,
        ],
    )

    assert "Using existing UI prompts with IDs" in _strip_ansi(result.output)
    assert "123" in _strip_ansi(result.output)
    assert "456" in _strip_ansi(result.output)
    assert "Creating UI prompts" not in _strip_ansi(result.output)
    assert "Scan created with id" in _strip_ansi(result.output)
    assert api_caller_mock.call_count == 1


def testRunScanCLI_withBothUIPromptsAndIds_combinesBothTypes(
    mocker: plugin.MockerFixture,
) -> None:
    """Test ostorlab ci_scan with both UI prompt IDs and named prompts combines both."""
    named_prompts_create_dict = {
        "data": {
            "createUiPrompts": {
                "uiPrompts": [
                    {"id": "789", "name": "New prompt", "code": "click button"},
                ]
            }
        }
    }
    scan_create_dict = {"data": {"createMobileScan": {"scan": {"id": "1"}}}}
    api_caller_mock = mocker.patch(
        "ostorlab.apis.runners.authenticated_runner.AuthenticatedAPIRunner.execute",
        side_effect=[named_prompts_create_dict, scan_create_dict],
    )
    mocker.patch.object(run.run, "SLEEP_CHECKS", 1)
    runner = CliRunner()

    result = runner.invoke(
        rootcli.rootcli,
        [
            "--api-key=12",
            "ci-scan",
            "run",
            "--scan-profile=full_scan",
            "--title=scan1",
            "--ui-prompt-id=123",
            "--ui-prompt-id=456",
            "--ui-prompt-name=New prompt",
            "--ui-prompt-action=click button",
            "android-apk",
            TEST_FILE_PATH,
        ],
    )

    assert "Using existing UI prompts with IDs" in _strip_ansi(result.output)
    assert "123" in _strip_ansi(result.output)
    assert "456" in _strip_ansi(result.output)
    assert "Creating UI prompts" in _strip_ansi(result.output)
    assert "Created UI prompts with IDs" in _strip_ansi(result.output)
    assert "789" in _strip_ansi(result.output)
    assert "Scan created with id" in _strip_ansi(result.output)
    assert api_caller_mock.call_count == 2


def testRunScanCLI_withNamedUIPrompts_createsNamedPrompts(
    mocker: plugin.MockerFixture,
) -> None:
    """Test ostorlab ci_scan with named UI prompts creates prompts with names and actions."""
    named_prompts_create_dict = {
        "data": {
            "createUiPrompts": {
                "uiPrompts": [
                    {"id": "789", "name": "Login Test", "code": "click login button"},
                    {"id": "790", "name": "Navigation Test", "code": "navigate menu"},
                ]
            }
        }
    }
    scan_create_dict = {"data": {"createMobileScan": {"scan": {"id": "1"}}}}
    api_caller_mock = mocker.patch(
        "ostorlab.apis.runners.authenticated_runner.AuthenticatedAPIRunner.execute",
        side_effect=[named_prompts_create_dict, scan_create_dict],
    )
    mocker.patch.object(run.run, "SLEEP_CHECKS", 1)
    runner = CliRunner()

    result = runner.invoke(
        rootcli.rootcli,
        [
            "--api-key=12",
            "ci-scan",
            "run",
            "--scan-profile=full_scan",
            "--title=scan1",
            "--ui-prompt-name=Login Test",
            "--ui-prompt-action=click login button",
            "--ui-prompt-name=Navigation Test",
            "--ui-prompt-action=navigate menu",
            "android-apk",
            TEST_FILE_PATH,
        ],
    )

    assert "Creating UI prompts" in _strip_ansi(result.output)
    assert "Created UI prompts with IDs" in _strip_ansi(result.output)
    assert "789" in _strip_ansi(result.output)
    assert "790" in _strip_ansi(result.output)
    assert "Scan created with id" in _strip_ansi(result.output)
    assert api_caller_mock.call_count == 2
    named_prompts_call = api_caller_mock.call_args_list[0]
    assert named_prompts_call.args[0]._ui_prompts == [
        {"name": "Login Test", "code": "click login button"},
        {"name": "Navigation Test", "code": "navigate menu"},
    ]


def testRunScanCLI_withMismatchedNamedPrompts_showsError(
    mocker: plugin.MockerFixture,
) -> None:
    """Test ostorlab ci_scan with mismatched named prompts shows error."""
    runner = CliRunner()

    result = runner.invoke(
        rootcli.rootcli,
        [
            "--api-key=12",
            "ci-scan",
            "run",
            "--scan-profile=full_scan",
            "--title=scan1",
            "--ui-prompt-name=Login Test",
            "--ui-prompt-action=click login button",
            "--ui-prompt-action=navigate menu",  # Extra action without name
            "android-apk",
            TEST_FILE_PATH,
        ],
    )

    assert "UI prompt names and actions are not matching count" in _strip_ansi(
        result.output
    )
    assert isinstance(result.exception, BaseException)
