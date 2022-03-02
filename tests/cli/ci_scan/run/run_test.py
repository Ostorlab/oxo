"""Tests for scan run command."""
from click.testing import CliRunner
from ostorlab.cli.ci_scan import run
from ostorlab.cli import rootcli


def testRunScanCLI_WhenApiKeyIsMissing_ShowError(mocker):
    """Test ostorlab ci_scan with no api key. it should exit with error exit_code = 2."""
    mocker.patch('ostorlab.apis.runners.authenticated_runner.AuthenticatedAPIRunner.execute', return_value=True)
    runner = CliRunner()
    result = runner.invoke(rootcli.rootcli,
                           ['ci-scan', 'run', '--plan=free',
                            '--title=scan1', 'android', 'tests/conftest.py'])

    assert isinstance(result.exception, BaseException)
    assert 'API key not not provided.' in result.output


def testRunScanCLI_whenBreakOnRiskRatingIsNotSet_ReturnsIdScan(mocker):
    """Test ostorlab ci_scan with no break_on_risk_rating. it should create the scan and returns its id."""
    scan_create_dict = {
        'data': {
            'scan': {
                        'id': 1,
                    }
            }
        }
    mocker.patch('ostorlab.apis.runners.authenticated_runner.AuthenticatedAPIRunner.execute',
                 return_value=scan_create_dict)
    runner = CliRunner()
    result = runner.invoke(rootcli.rootcli,
                           ['--api_key=12', 'ci-scan', 'run', '--plan=rapid_static','--title=scan1',
                            'android', 'tests/conftest.py'])

    assert 'Scan created with id 1.' in result.output


def testRunScanCLI_whenBreakOnRiskRatingIsSetWithInvalidValue_ShowError(mocker):
    """Test ostorlab ci_scan with invalid break_on_risk_rating. it should exit with error exit_code = 2."""
    scan_create_dict = {
        'data': {
            'scan': {
                        'id': 1,
                    }
            }
        }
    mocker.patch('ostorlab.apis.runners.authenticated_runner.AuthenticatedAPIRunner.execute',
                 return_value=scan_create_dict)
    runner = CliRunner()
    result = runner.invoke(rootcli.rootcli,
                           ['--api_key=12', 'ci-scan', 'run', '--plan=rapid_static',
                            '--break_on_risk_rating=toto', '--title=scan1',
                            'ios', 'tests/conftest.py'])

    assert 'Scan created with id 1.' in result.output
    assert 'Incorrect risk rating value toto.' in result.output
    assert isinstance(result.exception, BaseException)


def testRunScanCLI_whenBreakOnRiskRatingIsSetAndScanTimeout_WaitScan(mocker):
    """Test ostorlab ci_scan with invalid break_on_risk_rating. it should exit with error exit_code = 2."""
    scan_create_dict = {
        'data': {
            'scan': {
                        'id': 1,
                    }
            }
        }

    scan_info_dict = {
        'data': {
            'scan': {
                        'progress': 'not_started',
                        'riskRating': 'info',
                    }
            }
        }
    mocker.patch('ostorlab.apis.runners.authenticated_runner.AuthenticatedAPIRunner.execute',
                 side_effect=[scan_create_dict, scan_info_dict, scan_info_dict, scan_info_dict, scan_info_dict])
    mocker.patch.object(run.run, 'MINUTE', 1)
    mocker.patch.object(run.run, 'SLEEP_CHECKS', 5)

    runner = CliRunner()
    result = runner.invoke(rootcli.rootcli,
                           ['--api_key=12', 'ci-scan', 'run', '--plan=rapid_static',
                            '--break_on_risk_rating=medium', '--max_wait_minutes=1' ,'--title=scan1',
                            'android', 'tests/conftest.py'])

    assert 'Scan created with id 1.' in result.output
    assert 'The scan is still running.' in result.output
    assert isinstance(result.exception, BaseException)


def testRunScanCLI_whenBreakOnRiskRatingIsSetAndScanDone_ScanDone(mocker):
    """Test ostorlab ci_scan with invalid break_on_risk_rating. it should exit with error exit_code = 2."""
    scan_create_dict = {
        'data': {
            'scan': {
                        'id': 1,
                    }
            }
        }

    scan_info_dict = {
        'data': {
            'scan': {
                        'progress': 'done',
                        'riskRating': 'info',
                    }
            }
        }
    mocker.patch('ostorlab.apis.runners.authenticated_runner.AuthenticatedAPIRunner.execute',
                 side_effect=[scan_create_dict, scan_info_dict, scan_info_dict])
    mocker.patch.object(run.run, 'SLEEP_CHECKS', 1)

    runner = CliRunner()
    result = runner.invoke(rootcli.rootcli,
                           ['--api_key=12', 'ci-scan', 'run', '--plan=rapid_static',
                            '--break_on_risk_rating=low', '--max_wait_minutes=10' ,'--title=scan1',
                            'android','tests/conftest.py'])

    assert 'Scan created with id 1.' in result.output
    assert 'Scan done with risk rating info.' in result.output


def testRunScanCLI_whenBreakOnRiskRatingIsSetAndScanDoneHigherRisk_ShowError(mocker):
    """Test ostorlab ci_scan with invalid break_on_risk_rating. it should exit with error exit_code = 2."""
    scan_create_dict = {
        'data': {
            'scan': {
                        'id': 1,
                    }
            }
        }

    scan_info_dict = {
        'data': {
            'scan': {
                        'progress': 'done',
                        'riskRating': 'high',
                    }
            }
        }
    mocker.patch('ostorlab.apis.runners.authenticated_runner.AuthenticatedAPIRunner.execute',
                 side_effect=[scan_create_dict, scan_info_dict, scan_info_dict])
    mocker.patch.object(run.run, 'SLEEP_CHECKS', 1)

    runner = CliRunner()
    result = runner.invoke(rootcli.rootcli,
                           ['--api_key=12', 'ci-scan', 'run', '--plan=rapid_static',
                            '--break_on_risk_rating=medium', '--max_wait_minutes=10' ,'--title=scan1',
                            'ios', 'tests/conftest.py'])

    assert 'Scan created with id 1.' in result.output
    assert 'The scan risk rating is high.' in result.output
    assert isinstance(result.exception, BaseException)



def testRunScanCLI_whithLogLfavorGithub_PrintExpctedOutput(mocker):
    """Test ostorlab ci_scan with invalid break_on_risk_rating. it should exit with error exit_code = 2."""
    scan_create_dict = {
        'data': {
            'scan': {
                        'id': 1,
                    }
            }
        }

    scan_info_dict = {
        'data': {
            'scan': {
                        'progress': 'done',
                        'riskRating': 'high',
                    }
            }
        }
    mocker.patch('ostorlab.apis.runners.authenticated_runner.AuthenticatedAPIRunner.execute',
                 side_effect=[scan_create_dict, scan_info_dict, scan_info_dict])
    mocker.patch.object(run.run, 'SLEEP_CHECKS', 1)

    runner = CliRunner()
    result = runner.invoke(rootcli.rootcli,
                           ['--api_key=12', 'ci-scan', 'run', '--plan=rapid_static',
                            '--break_on_risk_rating=medium', '--max_wait_minutes=10' ,'--title=scan1',
                            '--log_flavor=github', 'ios', 'tests/conftest.py'])

    assert 'Scan created with id 1.' in result.output
    assert '::set-output name=scan_id::1' in result.output
    assert 'The scan risk rating is high.' in result.output
    assert isinstance(result.exception, BaseException)
