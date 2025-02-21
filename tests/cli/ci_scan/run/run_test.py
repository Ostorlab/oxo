"""Tests for scan run command."""

import os
import pathlib

from click.testing import CliRunner
from pytest_mock import plugin

from ostorlab.cli import rootcli
from ostorlab.cli.ci_scan import run

TEST_FILE_PATH = str(pathlib.Path(__file__).parent / "test_file")


def testRunScanCLI_WhenApiKeyIsMissing_ShowError(mocker):
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
    assert "API key not not provided." in result.output


def testRunScanCLI_whenBreakOnRiskRatingIsNotSet_ReturnsIdScan(mocker):
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

    assert "Scan created with id 1." in result.output


def testRunScanCLI_whenBreakOnRiskRatingIsSetWithInvalidValue_ShowError(mocker):
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

    assert "Scan created with id 1." in result.output
    assert "Incorrect risk rating value toto." in result.output
    assert isinstance(result.exception, BaseException)


def testRunScanCLI_whenBreakOnRiskRatingIsSetAndScanTimeout_WaitScan(mocker):
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
        side_effect=[
            scan_create_dict,
            scan_info_dict,
            scan_info_dict,
            scan_info_dict,
            scan_info_dict,
        ],
    )
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

    assert "Scan created with id 1." in result.output
    assert "The scan is still running." in result.output
    assert isinstance(result.exception, BaseException)


def testRunScanCLI_whenBreakOnRiskRatingIsSetAndScanDone_ScanDone(mocker):
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

    assert "Scan created with id 1." in result.output
    assert "Scan done with risk rating info." in result.output


def testRunScanCLI_whenBreakOnRiskRatingIsSetAndScanDoneHigherRisk_ShowError(mocker):
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

    assert "Scan created with id 1." in result.output
    assert "The scan risk rating is high." in result.output
    assert isinstance(result.exception, BaseException)


def testRunScanCLI_whithLogLfavorGithub_PrintExpctedOutput(mocker):
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

    assert "Scan created with id 1." in result.output
    assert "::set-output name=scan_id::1" in result.output
    assert "The scan risk rating is high." in result.output
    assert isinstance(result.exception, BaseException)


def testRunScanCLI_withTestCredentials_callsCreateTestCredentials(mocker):
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
    assert "Created test credentials" in result.output
    assert "Scan created with id 1." in result.output
    assert "password='pass'" not in result.output
    assert "************" in result.output


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


def testRunScanCLI_withsboms_callApi(mocker: plugin.MockerFixture, httpx_mock) -> None:
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
    mocker: plugin.MockerFixture, httpx_mock
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
