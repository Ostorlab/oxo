"""Tests for vulnz describe command."""

from click.testing import CliRunner

from ostorlab.apis.runners import authenticated_runner
from ostorlab.cli import rootcli
from ostorlab.runtimes.local.models import models


def testOstorlabVulnzDescribeCLI_whenCorrectCommandsAndOptionsProvided_showsVulnzInfo(
    mocker, db_engine_path
):
    """Test ostorlab vulnz describe command with correct commands and options.
    Should show vulnz details.
    """
    runner = CliRunner()
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    create_scan_db = models.Scan.create("test")
    vuln_db = models.Vulnerability.create(
        title="Secure TLS certificate validation",
        short_description="Application performs proper server certificate "
        "validation",
        description="The application performs proper TLS certificate validation.",
        recommendation="The implementation is secure, no recommendation apply.",
        technical_detail="TLS certificate validation was tested dynamically by "
        "intercepting traffic and presenting an invalid "
        "certificate. The application refuses to complete TLS "
        "negotiation when the certificate is not signed by "
        "valid authority.",
        risk_rating="HIGH",
        cvss_v3_vector="5:6:7",
        dna="121312",
        location={
            "android_store": {"package_name": "a.b.c"},
            "metadata": [{"type": "CODE_LOCATION", "value": "dir/file.js:41"}],
        },
        scan_id=create_scan_db.id,
    )

    result = runner.invoke(
        rootcli.rootcli, ["vulnz", "describe", "-v", str(vuln_db.id)]
    )

    assert vuln_db.scan_id is not None
    assert result.exception is None
    assert "The application performs" in result.output
    assert "TLS certificate validation" in result.output
    assert "a.b.c" in result.output


def testOstorlabCloudRuntimeScanVulnzDescribeCLI_whenCorrectCommandsAndOptionsProvided_showsVulnzInfo(
    httpx_mock,
):
    """Test ostorlab describe command when Correct command and correct scan id should show list of vulnz."""
    mock_response = {
        "data": {
            "scan": {
                "isEditable": "true",
                "vulnerabilities": {
                    "pageInfo": {
                        "hasNext": "false",
                        "hasPrevious": "false",
                        "count": 3,
                        "numPages": 1,
                    },
                    "vulnerabilities": [
                        {
                            "id": "38311495",
                            "technicalDetail": "<code>malwarebytes.keystone.permission.PERMISSION.CHECK_REQ</code> "
                            "not declared in <code>permission</code> tag",
                            "technicalDetailFormat": "HTML",
                            "customRiskRating": "MEDIUM",
                            "customCvssV3BaseScore": "null",
                            "falsePositive": "false",
                            "detail": {
                                "title": "Undeclared Permissions",
                                "shortDescription": "Custom permissions used in <activity> <service> <provider> "
                                "<receiver> tags, but not declared  in <permission> tag",
                                "description": "Applications can expose their functionality to other apps by defining ",
                                "recommendation": "Before applying a permission on any component, make sure it is "
                                "declared using `<permission>` element.\n\nFor example, an app that "
                                "wants to control who can start one of its activities could declare ",
                                "cvssV3Vector": "null",
                                "references": [
                                    {
                                        "title": "Typo in permission name allows to write contacts without user ",
                                        "url": "https://hackerone.com/reports/440749",
                                    }
                                ],
                            },
                            "vulnerabilityLocation": {
                                "asset": {"bundleId": "a.b.c"},
                                "metadata": [
                                    {
                                        "metadataType": "FILE_PATH",
                                        "metadataValue": "line:24,5",
                                    }
                                ],
                            },
                        }
                    ],
                },
            }
        }
    }
    httpx_mock.add_response(
        method="POST",
        url=authenticated_runner.AUTHENTICATED_GRAPHQL_ENDPOINT,
        json=mock_response,
        status_code=200,
    )
    runner = CliRunner()

    result = runner.invoke(
        rootcli.rootcli, ["vulnz", "--runtime", "cloud", "describe", "-scan-id=502152"]
    )

    assert "Applications can expose their functionality to other apps" in result.output
    assert "Vulnerabilities listed successfully" in result.output
    assert (
        "Typo in permission name allows to write contacts without user" in result.output
    )
    assert "a.b.c" in result.output


def testOstorlabCloudRuntimeScanVulnzDescribeCLI_whenScanNotFound_showNotFoundError(
    httpx_mock,
):
    """Test ostorlab describe command when Correct command and scan does not exist."""
    mock_response = {
        "errors": [
            {
                "message": "Scan matching query does not exist.",
                "locations": [{"line": 2, "column": 13}],
                "path": ["scan"],
            }
        ]
    }
    httpx_mock.add_response(
        method="POST",
        url=authenticated_runner.AUTHENTICATED_GRAPHQL_ENDPOINT,
        json=mock_response,
        status_code=200,
    )
    runner = CliRunner()

    result = runner.invoke(
        rootcli.rootcli, ["vulnz", "--runtime", "cloud", "describe", "-scan-id=502152"]
    )

    assert "Vulnerability / scan not Found." in result.output
