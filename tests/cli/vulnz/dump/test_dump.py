"""Unittest for vulnz dump command."""

import csv
import json
import pathlib

from click.testing import CliRunner

from ostorlab.apis.runners import authenticated_runner
from ostorlab.cli import rootcli
from ostorlab.runtimes.local.models import models


def testVulnzDump_whenOptionsAreValid_jsonOutputFileIsCreated(
    mocker, tmpdir, db_engine_path
):
    """Test ostorlab vulnz dump command with correct commands and options.
    Should create a json file with the vulnerabilities.

    tmpdir : pytest fixture for temporary paths & files.
    """

    runner = CliRunner()
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    create_scan_db = models.Scan.create(title="test", asset="android")
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
            "android_store": {"package_name": "a.b.c"},
            "metadata": [{"type": "CODE_LOCATION", "value": "dir/file.js:41"}],
        },
        scan_id=create_scan_db.id,
    )
    models.Vulnerability.create(
        title="OtherVuln",
        short_description="Xss",
        description="Javascript Vuln",
        recommendation="Sanitize data",
        technical_detail="a=$input",
        risk_rating="HIGH",
        cvss_v3_vector="5:6:7",
        dna="121312",
        scan_id=create_scan_db.id,
    )
    output_file = pathlib.Path(tmpdir) / "output.jsonl"

    result = runner.invoke(
        rootcli.rootcli,
        [
            "vulnz",
            "dump",
            "-s",
            str(vuln_db.scan_id),
            "-o",
            str(output_file),
            "-f",
            "jsonl",
        ],
    )

    assert result.exception is None
    assert "Vulnerabilities saved" in result.output
    with open(output_file, "r", encoding="utf-8") as f:
        data = []
        for obj in f:
            data.append(json.loads(obj))
    assert data[0]["id"] == 1
    assert data[0]["risk_rating"] == "High"
    assert data[0]["cvss_v3_vector"] == "5:6:7"
    assert data[0]["title"] == "MyVuln"
    assert "Android: `a.b.c`" in data[0]["location"]
    assert data[1]["id"] == 2
    assert data[1]["risk_rating"] == "High"
    assert data[1]["title"] == "OtherVuln"


def testVulnzDumpCloudRuntime_whenOptionsAreValid_jsonOutputFileIsCreated(
    requests_mock, tmpdir
):
    """Test ostorlab vulnz dump command with correct commands and options and the selected runtime is cloud.
    Should create a json file with the vulnerabilities.

    tmpdir : pytest fixture for temporary paths & files.
    """
    list_vulnz = {
        "data": {
            "scan": {
                "vulnerabilities": {
                    "pageInfo": {"hasNext": False, "numPages": 2},
                    "vulnerabilities": [
                        {
                            "id": "37200006",
                            "technicalDetail": "someData",
                            "detail": {
                                "title": "Use of Outdated Vulnerable Component",
                                "shortDescription": "The application uses an outdated "
                                "component or library with "
                                "publicly known vulnerabilities",
                                "description": "someDescription",
                                "recommendation": "someRecommendation",
                                "cvssV3Vector": None,
                                "riskRating": "LOW",
                                "references": [
                                    {
                                        "title": "dummy title",
                                        "url": "https://dummy.co/dummy2",
                                    }
                                ],
                            },
                            "vulnerabilityLocation": {
                                "asset": {"packageName": "a.b.c"},
                                "metadata": [
                                    {
                                        "metadataType": "CODE_LOCATION",
                                        "metadataValue": "some/file.java:42",
                                    }
                                ],
                            },
                        },
                        {
                            "id": "37199942",
                            "technicalDetail": "someData",
                            "detail": {
                                "title": "Use of Outdated Vulnerable Component",
                                "shortDescription": "The application uses an outdated "
                                "component or library with "
                                "publicly known vulnerabilities",
                                "description": "someDescription",
                                "recommendation": "someRecommendation",
                                "cvssV3Vector": None,
                                "riskRating": "LOW",
                            },
                        },
                    ],
                }
            }
        }
    }

    requests_mock.post(
        authenticated_runner.AUTHENTICATED_GRAPHQL_ENDPOINT,
        json=list_vulnz,
        status_code=200,
    )

    runner = CliRunner()
    output_file = pathlib.Path(tmpdir) / "output.jsonl"
    result = runner.invoke(
        rootcli.rootcli,
        [
            "vulnz",
            "--runtime",
            "cloud",
            "dump",
            "-s",
            "5858",
            "-o",
            str(output_file),
            "-f",
            "jsonl",
        ],
    )

    assert result.exception is None
    assert "Vulnerabilities saved to" in result.output
    with open(output_file, "r", encoding="utf-8") as f:
        data = []
        for obj in f:
            data.append(json.loads(obj))
    assert data[0]["id"] == "37200006"
    assert "Use of Outdated Vulnerable Component" in data[0]["title"]
    assert "dummy title: https://dummy.co/dummy2" in data[0]["references"]
    assert "Android package name: a.b.c" in data[0]["location"]


def testVulnzDumpCloudRuntime_whenOptionsAreValid_csvOutputFileIsCreated(
    requests_mock, tmpdir
):
    """Test ostorlab vulnz dump command with correct commands and options and runtime is cloud.
    Should create a json file with the vulnerabilities.

    tmpdir : pytest fixture for temporary paths & files.
    """
    list_vulnz = {
        "data": {
            "scan": {
                "vulnerabilities": {
                    "pageInfo": {"hasNext": False, "numPages": 1},
                    "vulnerabilities": [
                        {
                            "id": "37200006",
                            "technicalDetail": "someData",
                            "detail": {
                                "title": "Use of Outdated Vulnerable Component",
                                "shortDescription": "The application uses an outdated component or library with "
                                "publicly known vulnerabilities",
                                "description": "someDescription",
                                "recommendation": "someRecommendation",
                                "cvssV3Vector": "None",
                                "riskRating": "LOW",
                                "references": [
                                    {"title": "title1", "url": "https://url1.co/page2"}
                                ],
                            },
                        },
                        {
                            "id": "37199942",
                            "technicalDetail": "someData",
                            "detail": {
                                "title": "Use of Outdated Vulnerable Component",
                                "shortDescription": "The application uses an outdated "
                                "component or library with "
                                "publicly known vulnerabilities",
                                "description": "someDescription",
                                "recommendation": "someRecommendation",
                                "cvssV3Vector": "None",
                                "riskRating": "LOW",
                            },
                        },
                    ],
                }
            }
        }
    }

    requests_mock.post(
        authenticated_runner.AUTHENTICATED_GRAPHQL_ENDPOINT,
        json=list_vulnz,
        status_code=200,
    )

    runner = CliRunner()
    output_file = pathlib.Path(tmpdir) / "output.csv"
    result = runner.invoke(
        rootcli.rootcli,
        [
            "vulnz",
            "--runtime",
            "cloud",
            "dump",
            "-s",
            "2",
            "-o",
            str(output_file),
            "-f",
            "csv",
        ],
    )
    assert result.exception is None
    with output_file.open("r", encoding="utf-8") as file:
        csvreader = csv.reader(file)
        header = next(csvreader)
        data = []
        for row in csvreader:
            if row:
                data.append(row)

    assert result.exception is None
    assert "Vulnerabilities saved to" in result.output
    assert header == [
        "id",
        "title",
        "location",
        "risk_rating",
        "cvss_v3_vector",
        "short_description",
        "description",
        "recommendation",
        "references",
        "technical_detail",
    ]
    assert data[0][3] == "LOW"
    assert "title1: https://url1.co/page2" in data[0][-2]


def testVulnzDumpCloudRuntime_whenScanNotfound_ShowError(requests_mock, tmpdir):
    """Test ostorlab vulnz dump command with correct commands and wrong scan id.
    Should show not found error.

    tmpdir : pytest fixture for temporary paths & files.
    """
    list_vulnz = {
        "errors": [
            {
                "message": "Scan matching query does not exist.",
                "locations": [{"line": 2, "column": 13}],
                "path": ["scan"],
            }
        ],
        "data": {"scan": "null"},
    }

    requests_mock.post(
        authenticated_runner.AUTHENTICATED_GRAPHQL_ENDPOINT,
        json=list_vulnz,
        status_code=200,
    )

    runner = CliRunner()
    output_file = pathlib.Path(tmpdir) / "output.jsonl"
    result = runner.invoke(
        rootcli.rootcli,
        [
            "vulnz",
            "--runtime",
            "cloud",
            "dump",
            "-s",
            "5858",
            "-o",
            str(output_file),
            "-f",
            "jsonl",
        ],
    )
    assert result.exception is None
    assert "ERROR: scan with id 5858 does not exist" in result.output


def testVulnzDump_whenOptionsAreValid_csvOutputFileIsCreated(
    mocker, tmpdir, db_engine_path
):
    """Test ostorlab vulnz dump command with correct commands and options.
    Should create a csv file with the vulnerabilities.

    tmpdir : pytest fixture for temporary paths & files.
    """

    runner = CliRunner()
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    create_scan_db = models.Scan.create(title="test", asset="Android")
    vuln_db = models.Vulnerability.create(
        title="MyVuln",
        short_description="Xss",
        description="Javascript Vuln",
        recommendation="Sanitize data",
        technical_detail="a=$input",
        risk_rating="HIGH",
        cvss_v3_vector="5:6:7",
        dna="121312",
        references=[{"title": "dummy title", "url": "https://dummy.co/path"}],
        location={
            "android_store": {"package_name": "a.b.c"},
            "metadata": [{"type": "CODE_LOCATION", "value": "dir/file.js:41"}],
        },
        scan_id=create_scan_db.id,
    )

    output_file = pathlib.Path(tmpdir) / "output.csv"

    result = runner.invoke(
        rootcli.rootcli,
        [
            "vulnz",
            "dump",
            "-s",
            str(vuln_db.scan_id),
            "-o",
            str(output_file),
            "-f",
            "csv",
        ],
    )
    with output_file.open("r", encoding="utf-8") as file:
        csvreader = csv.reader(file)
        header = next(csvreader)
        data = []
        for row in csvreader:
            if row:
                data.append(row)

    assert result.exception is None
    assert "Vulnerabilities saved" in result.output
    assert header == [
        "id",
        "title",
        "location",
        "risk_rating",
        "cvss_v3_vector",
        "short_description",
        "description",
        "recommendation",
        "references",
        "technical_detail",
    ]
    assert data[0][3] == "High"
    assert "Android: `a.b.c`" in data[0][2]
    assert "dummy title: https://dummy.co/path" in data[0][-2]


def testVulnzDumpInOrderOfSeverity_whenOptionsAreValid_jsonOutputFileIsCreated(
    mocker, tmpdir, db_engine_path
):
    """Test ostorlab vulnz dump command with correct commands and options.
    Should create a json file with the vulnerabilities, ordered by the risk severity.

    tmpdir : pytest fixture for temporary paths & files.
    """
    runner = CliRunner()
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    create_scan_db = models.Scan.create(title="test", asset="Android")

    vuln_db = models.Vulnerability.create(
        title="MyVuln",
        short_description="Xss",
        description="Javascript Vuln",
        recommendation="Sanitize data",
        technical_detail="a=$input",
        risk_rating="HARDENING",
        cvss_v3_vector="5:6:7",
        dna="121312",
        scan_id=create_scan_db.id,
    )

    output_file = pathlib.Path(tmpdir) / "output.jsonl"
    result = runner.invoke(
        rootcli.rootcli,
        [
            "vulnz",
            "dump",
            "-s",
            str(vuln_db.scan_id),
            "-o",
            str(output_file),
            "-f",
            "jsonl",
        ],
    )

    assert "Vulnerabilities saved" in result.output
    with open(output_file, "r", encoding="utf-8") as f:
        data = []
        for obj in f:
            data.append(json.loads(obj))
    assert "MyVuln" in data[0]["title"]
    assert data[0]["risk_rating"] == "Hardening"
    assert data[0]["id"] == 1
