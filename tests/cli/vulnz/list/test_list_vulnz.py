"""Tests for vulnz list command."""

from click.testing import CliRunner
from pytest_mock import plugin

from ostorlab.apis.runners import authenticated_runner
from ostorlab.cli import rootcli
from ostorlab.runtimes.local.models import models


def testOstorlabVulnzListCLI_whenCorrectCommandsAndOptionsProvidedAndRuntimeIsLocal_showsVulnzInfo(
    mocker, db_engine_path
):
    """Test oxo vulnz list command with correct commands and options.
    Should show vulnz information.
    """
    runner = CliRunner()
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    create_scan_db = models.Scan.create("test")
    vuln_db = models.Vulnerability.create(
        title="MyVuln",
        short_description="Xss",
        description="Javascript Vuln",
        recommendation="Sanitize data",
        technical_detail="a=$input",
        risk_rating="HIGH",
        cvss_v3_vector="5:6:7",
        dna="121312",
        location={
            "domain_name": {"name": "dummy.co"},
            "metadata": [{"type": "URL", "value": "https://dummy.co/dummy"}],
        },
        scan_id=create_scan_db.id,
        references=[],
    )
    result = runner.invoke(
        rootcli.rootcli, ["vulnz", "list", "-s", str(vuln_db.scan_id)]
    )

    assert vuln_db.scan_id is not None
    assert result.exception is None
    assert "MyVuln" in result.output
    assert "High" in result.output
    assert "https://dummy" in result.output


def testOstorlabVulnzListCLI_ScanNotFoundAndRuntimeCloud_showsNotFoundError(
    httpx_mock,
):
    """Ensure the vulnz list cli command correctly handles case where the scan is not found by the API."""
    mock_response = {
        "errors": [
            {
                "message": "Scan matching query does not exist.",
                "locations": [{"line": 2, "column": 13}],
                "path": ["scan"],
            }
        ],
    }
    runner = CliRunner()
    httpx_mock.add_response(
        method="POST",
        url=authenticated_runner.AUTHENTICATED_GRAPHQL_ENDPOINT,
        json=mock_response,
        status_code=401,
    )
    result = runner.invoke(
        rootcli.rootcli, ["vulnz", "--runtime", "cloud", "list", "--scan-id", "56835"]
    )
    assert "ERROR: scan with id 56835 does not exist." in result.output, result.output


def testOstorlabVulnzListCLI_WhenRuntimeCloudAndValiScanID_showsVulnzInfo(
    httpx_mock,
):
    """Ensure the vulnz list cli command displays the vulnerabilities information correctly."""
    mock_response = {
        "data": {
            "scan": {
                "vulnerabilities": {
                    "vulnerabilities": [
                        {
                            "id": "38312829",
                            "detail": {
                                "title": "Intent Spoofing",
                                "shortDescription": "The application is vulnerable to intent spoofing which ..",
                                "cvssV3Vector": "CVSS:3.0/AV:L/AC:H/PR:H/UI:N/S:U/C:H/I:H/A:H",
                                "riskRating": "POTENTIALLY",
                            },
                        },
                        {
                            "id": "38312828",
                            "detail": {
                                "title": "Intent Spoofing",
                                "shortDescription": "The application is vulner...",
                                "cvssV3Vector": "CVSS:3.0/AV:L/AC:H/PR:H/UI:N/S:U/C:H/I:H/A:H",
                                "riskRating": "POTENTIALLY",
                            },
                        },
                    ]
                }
            }
        }
    }
    runner = CliRunner()
    httpx_mock.add_response(
        method="POST", url="https://api.ostorlab.co/apis/graphql", json=mock_response
    )
    result = runner.invoke(
        rootcli.rootcli, ["vulnz", "--runtime", "cloud", "list", "--scan-id", "56835"]
    )
    assert "Title" in result.output, result.output
    assert "Scan 56835: Found 2 vulnerabilities" in result.output, result.output


def testOstorlabVulnzListCLI_whenFilterByRiskRatingAndRuntimeIsLocal_showsCorrectResult(
    mocker: plugin.MockerFixture,
    db_engine_path: str,
) -> None:
    """Test oxo vulnz list command with filter by risk rating and runtime is local.
    Should show the correct results."""
    runner = CliRunner()
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    create_scan_db = models.Scan.create("test")
    models.Vulnerability.create(
        title="Remote command execution",
        short_description="Remote command execution",
        description="Remote command execution",
        recommendation="Sanitize data",
        technical_detail="a=$input",
        risk_rating="HIGH",
        cvss_v3_vector="5:6:7",
        dna="121312",
        location={
            "domain_name": {"name": "dummy.co"},
            "metadata": [{"type": "URL", "value": "https://dummy.co/dummy"}],
        },
        scan_id=create_scan_db.id,
        references=[],
    )
    models.Vulnerability.create(
        title="List of dynamic code loading API calls",
        short_description="List of dynamic code loading API calls",
        description="List of dynamic code loading API calls",
        recommendation="Sanitize data",
        technical_detail="a=$input",
        risk_rating="INFO",
        cvss_v3_vector="5:6:7",
        dna="121312",
        location={
            "domain_name": {"name": "dummy.co"},
            "metadata": [{"type": "URL", "value": "https://dummy.co/dummy"}],
        },
        scan_id=create_scan_db.id,
        references=[],
    )
    models.Vulnerability.create(
        title="The application calls the registerReceiver method with the argument flags set to RECEIVER_EXPORTED",
        short_description="The application calls the registerReceiver method with the argument flags set to RECEIVER_EXPORTED",
        description="The application calls the registerReceiver method with the argument flags set to RECEIVER_EXPORTED",
        recommendation="Sanitize data",
        technical_detail="a=$input",
        risk_rating="MEDIUM",
        cvss_v3_vector="5:6:7",
        dna="121312",
        location={
            "domain_name": {"name": "dummy.co"},
            "metadata": [{"type": "URL", "value": "https://dummy.co/dummy"}],
        },
        scan_id=create_scan_db.id,
        references=[],
    )
    models.Vulnerability.create(
        title="Application is compiled with debug mode disabled",
        short_description="Application is compiled with debug mode disabled",
        description="Application is compiled with debug mode disabled",
        recommendation="Sanitize data",
        technical_detail="a=$input",
        risk_rating="SECURE",
        cvss_v3_vector="5:6:7",
        dna="121312",
        location={
            "domain_name": {"name": "dummy.co"},
            "metadata": [{"type": "URL", "value": "https://dummy.co/dummy"}],
        },
        scan_id=create_scan_db.id,
        references=[],
    )

    result = runner.invoke(
        rootcli.rootcli,
        ["vulnz", "list", "-s", str(create_scan_db.id), "-r", "HIGH,info"],
    )

    assert result.exception is None
    assert "Scan 1: Found 2 vulnerabilities." in result.output
    assert "High" in result.output
    assert "Info" in result.output
    result_keywords = [
        "List of",
        "dynamic",
        "loading",
        "calls",
        "Remote",
        "command",
        "execution",
    ]
    assert all(word in result.output for word in result_keywords) is True


def testOstorlabVulnzListCLI_whenFilterBySearchAndRuntimeIsLocal_showsCorrectResult(
    mocker: plugin.MockerFixture,
    db_engine_path: str,
) -> None:
    """Test oxo vulnz list command with filter by search and runtime is local.
    Should show the correct results."""
    runner = CliRunner()
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    create_scan_db = models.Scan.create("test")
    models.Vulnerability.create(
        title="Remote command execution",
        short_description="Remote command execution",
        description="Remote command execution",
        recommendation="Sanitize data",
        technical_detail="a=$input",
        risk_rating="HIGH",
        cvss_v3_vector="5:6:7",
        dna="121312",
        location={
            "domain_name": {"name": "dummy.co"},
            "metadata": [{"type": "URL", "value": "https://dummy.co/dummy"}],
        },
        scan_id=create_scan_db.id,
        references=[],
    )

    result_title = runner.invoke(
        rootcli.rootcli,
        ["vulnz", "list", "-s", str(create_scan_db.id), "-sh", "command"],
    )
    result_tech_detail = runner.invoke(
        rootcli.rootcli,
        ["vulnz", "list", "-s", str(create_scan_db.id), "-sh", "input"],
    )

    assert result_title.exception is None
    assert "Scan 1: Found 1 vulnerabilities." in result_title.output
    assert "High" in result_title.output
    result_keywords = ["Remote", "command", "execution"]
    assert all(word in result_title.output for word in result_keywords) is True
    assert result_tech_detail.exception is None
    assert "Scan 1: Found 1 vulnerabilities." in result_tech_detail.output
    assert "High" in result_tech_detail.output
    result_keywords = ["Remote", "command", "execution"]
    assert all(word in result_tech_detail.output for word in result_keywords) is True


def testOstorlabVulnzListCLI_whenFilterByRiskRatingAndRuntimeIsCloud_showsCorrectResult(
    httpx_mock,
) -> None:
    """Test oxo vulnz list command with filter by risk rating and runtime is cloud.
    Should show the correct result."""
    mock_response = {
        "data": {
            "scan": {
                "vulnerabilities": {
                    "vulnerabilities": [
                        {
                            "id": "38312829",
                            "vulnerabilityLocation": {
                                "asset": {"bundleId": "com.comerica.tmconnectmobile"},
                                "metadata": [],
                            },
                            "detail": {
                                "title": "Remote command execution",
                                "shortDescription": "Remote command execution",
                                "cvssV3Vector": "CVSS:3.0/AV:L/AC:H/PR:H/UI:N/S:U/C:H/I:H/A:H",
                                "riskRating": "HIGH",
                            },
                        },
                        {
                            "id": "38312828",
                            "vulnerabilityLocation": {
                                "asset": {
                                    "packageName": "com.firsttennessee.prepaid.vmcp"
                                },
                                "metadata": [],
                            },
                            "detail": {
                                "title": "List of dynamic code loading API calls",
                                "shortDescription": "List of dynamic code loading API calls",
                                "cvssV3Vector": "CVSS:3.0/AV:L/AC:H/PR:H/UI:N/S:U/C:H/I:H/A:H",
                                "riskRating": "INFO",
                            },
                        },
                        {
                            "id": "38312827",
                            "vulnerabilityLocation": {
                                "asset": {"name": "www.example.com"},
                                "metadata": [],
                            },
                            "detail": {
                                "title": "The application calls the registerReceiver method with the argument flags set to RECEIVER_EXPORTED",
                                "shortDescription": "The application calls the registerReceiver method with the argument flags set to RECEIVER_EXPORTED",
                                "cvssV3Vector": "CVSS:3.0/AV:L/AC:H/PR:H/UI:N/S:U/C:H/I:H/A:H",
                                "riskRating": "MEDIUM",
                            },
                        },
                        {
                            "id": "38312826",
                            "vulnerabilityLocation": {
                                "asset": {"host": "91.235.134.131"},
                                "metadata": [
                                    {"metadataType": "PORT", "metadataValue": "443"}
                                ],
                            },
                            "detail": {
                                "title": "Application is compiled with debug mode disabled",
                                "shortDescription": "Application is compiled with debug mode disabled",
                                "cvssV3Vector": "CVSS:3.0/AV:L/AC:H/PR:H/UI:N/S:U/C:H/I:H/A:H",
                                "riskRating": "SECURE",
                            },
                        },
                        {
                            "id": "38312825",
                            "vulnerabilityLocation": {
                                "asset": {
                                    "host": "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
                                },
                                "metadata": [],
                            },
                            "detail": {
                                "title": "Server Side Inclusion",
                                "shortDescription": "Server Side Inclusion",
                                "cvssV3Vector": "CVSS:3.0/AV:L/AC:H/PR:H/UI:N/S:U/C:H/I:H/A:H",
                                "riskRating": "CRITICAL",
                            },
                        },
                    ]
                }
            }
        }
    }
    runner = CliRunner()
    httpx_mock.add_response(
        method="POST", url="https://api.ostorlab.co/apis/graphql", json=mock_response
    )

    result = runner.invoke(
        rootcli.rootcli,
        [
            "vulnz",
            "--runtime",
            "cloud",
            "list",
            "--scan-id",
            "56835",
            "--risk-rating",
            "HIGH,info",
        ],
    )

    assert "Scan 56835: Found 2 vulnerabilities." in result.output
    assert "High" in result.output
    assert "Info" in result.output
    result_keywords = [
        "List",
        "dynamic",
        "loading",
        "calls",
        "Remote",
        "command",
        "execution",
    ]
    assert all(word in result.output for word in result_keywords) is True


def testOstorlabVulnzListCLI_whenFilterBySearchAndRuntimeIsCloud_showsCorrectResult(
    httpx_mock,
) -> None:
    """Test oxo vulnz list command with filter by search and runtime is cloud.
    Should show the correct result."""
    mock_response = {
        "data": {
            "scan": {
                "vulnerabilities": {
                    "vulnerabilities": [
                        {
                            "id": "38312829",
                            "technicalDetail": "a=$input",
                            "vulnerabilityLocation": {
                                "asset": {"bundleId": "com.comerica.tmconnectmobile"},
                                "metadata": [],
                            },
                            "detail": {
                                "title": "Remote command execution",
                                "shortDescription": "Remote command execution",
                                "cvssV3Vector": "CVSS:3.0/AV:L/AC:H/PR:H/UI:N/S:U/C:H/I:H/A:H",
                                "riskRating": "HIGH",
                                "description": "Remote command execution",
                                "recommendation": "Sanitize data",
                            },
                        },
                        {
                            "id": "38312828",
                            "technicalDetail": "a=$input",
                            "vulnerabilityLocation": {
                                "asset": {
                                    "packageName": "com.firsttennessee.prepaid.vmcp"
                                },
                                "metadata": [],
                            },
                            "detail": {
                                "title": "List of dynamic code loading API calls",
                                "shortDescription": "List of dynamic code loading API calls",
                                "cvssV3Vector": "CVSS:3.0/AV:L/AC:H/PR:H/UI:N/S:U/C:H/I:H/A:H",
                                "riskRating": "INFO",
                                "description": "List of dynamic code loading API calls",
                                "recommendation": "Sanitize data",
                            },
                        },
                    ]
                }
            }
        }
    }
    runner = CliRunner()
    httpx_mock.add_response(
        method="POST", url="https://api.ostorlab.co/apis/graphql", json=mock_response
    )

    result_title = runner.invoke(
        rootcli.rootcli,
        [
            "vulnz",
            "--runtime",
            "cloud",
            "list",
            "--scan-id",
            "56835",
            "--search",
            "command",
        ],
    )
    result_tech_detail = runner.invoke(
        rootcli.rootcli,
        [
            "vulnz",
            "--runtime",
            "cloud",
            "list",
            "--scan-id",
            "56835",
            "--search",
            "input",
        ],
    )

    assert "Scan 56835: Found 1 vulnerabilities." in result_title.output
    assert "High" in result_title.output
    result_title_keywords = ["Remote", "command", "execution"]
    assert all(word in result_title.output for word in result_title_keywords) is True
    assert "Scan 56835: Found 2 vulnerabilities." in result_tech_detail.output
    assert "High" in result_tech_detail.output
    assert "Info" in result_tech_detail.output
    result_tech_detail_keywords = [
        "Remote",
        "command",
        "execution",
        "dynamic",
        "loading",
        "calls",
    ]
    assert (
        all(word in result_tech_detail.output for word in result_tech_detail_keywords)
        is True
    )


def testOstorlabVulnzListCLI_whenListVulnz_showsVulnzOrderedByRiskRatingByDefault(
    scan_multiple_vulnz_different_risk_ratings: models.Scan,
    mocker: plugin.MockerFixture,
) -> None:
    """Test oxo vulnz list command orders vulnerabilities by risk rating."""
    runner = CliRunner()
    table_mock = mocker.patch("ostorlab.cli.console.Console.table")

    result = runner.invoke(
        rootcli.rootcli,
        ["vulnz", "list", "-s", str(scan_multiple_vulnz_different_risk_ratings.id)],
    )

    assert result.exception is None
    risk_ratings = [
        vuln.get("risk_rating") for vuln in table_mock.call_args_list[0][1].get("data")
    ]
    assert risk_ratings == [
        "[bold bright_white on #F55246]High[/]",
        "[bold bright_white on #FF9800]Medium[/]",
        "[bold bright_white on #FF9800]Medium[/]",
        "[bold bright_white on #FDDB45]Low[/]",
    ]


def testOstorlabVulnzListCLI_whenListVulnzOrderByID_showsVulnzOrderedByID(
    scan_multiple_vulnz_different_risk_ratings: models.Scan,
    mocker: plugin.MockerFixture,
) -> None:
    """Test oxo vulnz list command orders vulnerabilities by ID."""
    runner = CliRunner()
    table_mock = mocker.patch("ostorlab.cli.console.Console.table")

    result = runner.invoke(
        rootcli.rootcli,
        [
            "vulnz",
            "list",
            "-s",
            str(scan_multiple_vulnz_different_risk_ratings.id),
            "-o",
            "id",
        ],
    )

    assert result.exception is None
    ids = [vuln.get("id") for vuln in table_mock.call_args_list[0][1].get("data")]
    assert ids == ["1", "2", "3", "4"]


def testOstorlabVulnzListCLI_whenListVulnzOrderByTitle_showsVulnzOrderedByTitle(
    scan_multiple_vulnz_different_risk_ratings: models.Scan,
    mocker: plugin.MockerFixture,
) -> None:
    """Test oxo vulnz list command orders vulnerabilities by Title."""
    runner = CliRunner()
    table_mock = mocker.patch("ostorlab.cli.console.Console.table")

    result = runner.invoke(
        rootcli.rootcli,
        [
            "vulnz",
            "list",
            "-s",
            str(scan_multiple_vulnz_different_risk_ratings.id),
            "-o",
            "title",
        ],
    )

    assert result.exception is None
    titles = [vuln.get("title") for vuln in table_mock.call_args_list[0][1].get("data")]
    assert titles == [
        "vulnerability 1",
        "vulnerability 2",
        "vulnerability 3",
        "vulnerability 4",
    ]


def testOstorlabVulnzListCLI_whenListVulnzOrderByInvalidOption_showsErrorMessage(
    scan_multiple_vulnz_different_risk_ratings: models.Scan,
) -> None:
    """Test oxo vulnz list command orders vulnerabilities by Title."""
    runner = CliRunner()

    result = runner.invoke(
        rootcli.rootcli,
        [
            "vulnz",
            "list",
            "-s",
            str(scan_multiple_vulnz_different_risk_ratings.id),
            "-o",
            "invalid",
        ],
    )

    assert result.exception is not None
    assert (
        result.output.replace("\r\n", "\n")
        == """Usage: rootcli vulnz list [OPTIONS]
Try 'rootcli vulnz list --help' for help.

Error: Invalid value for '--order-by' / '-o': 'invalid' is not one of 'risk_rating', 'title', 'id'.
"""
    )
