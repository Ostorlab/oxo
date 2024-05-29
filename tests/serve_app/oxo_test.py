"""Unit tests for the oxo module."""

import io
import json

from flask import testing

from ostorlab.runtimes.local.models import models


def testImportScanMutation_always_shouldImportScan(
    client: testing.FlaskClient, zip_file_bytes: bytes
) -> None:
    """Test importScan mutation."""
    with models.Database() as session:
        nbr_scans_before_import = session.query(models.Scan).count()
        query = """
            mutation ImportScan($scanId: Int, $file: Upload!) {
                importScan(scanId: $scanId, file: $file) {
                    message
                }
            }
        """
        file_name = "imported_zip_file.zip"
        data = {
            "operations": json.dumps(
                {
                    "query": query,
                    "variables": {
                        "file": None,
                        "scanId": 20,
                    },
                }
            ),
            "map": json.dumps(
                {
                    "file": ["variables.file"],
                }
            ),
        }
        data["file"] = (io.BytesIO(zip_file_bytes), file_name)

        response = client.post(
            "/graphql", data=data, content_type="multipart/form-data"
        )

        assert response.status_code == 200, response.content
        response_json = response.get_json()
        nbr_scans_after_import = session.query(models.Scan).count()
        assert (
            response_json["data"]["importScan"]["message"]
            == "Scan imported successfully"
        )
        assert nbr_scans_after_import == nbr_scans_before_import + 1


def testQueryMultipleScans_always_shouldReturnMultipleScans(
    client: testing.FlaskClient, ios_scans: models.Scan
) -> None:
    """Test query for multiple scans."""
    with models.Database() as session:
        scans = session.query(models.Scan).filter(models.Scan.id.in_([1, 2])).all()
        assert scans is not None

    query = """
        query Scans($scanIds: [Int!]) {
            scans(scanIds: $scanIds) {
                scans {
                    id
                    title
                    asset
                    progress
                    createdTime
                }
            }
        }
    """

    response = client.post(
        "/graphql", json={"query": query, "variables": {"scanIds": [1, 2]}}
    )

    assert response.status_code == 200, response.get_json()
    scan1 = response.get_json()["data"]["scans"]["scans"][1]
    scan2 = response.get_json()["data"]["scans"]["scans"][0]
    assert scan1["id"] == "1"
    assert scan1["title"] == scans[0].title
    assert scan1["asset"] == scans[0].asset
    assert scan1["progress"] == scans[0].progress.name
    assert scan1["createdTime"] == scans[0].created_time.isoformat()
    assert scan2["id"] == "2"
    assert scan2["title"] == scans[1].title
    assert scan2["asset"] == scans[1].asset
    assert scan2["progress"] == scans[1].progress.name
    assert scan2["createdTime"] == scans[1].created_time.isoformat()


def testQueryMultipleScans_whenPaginationAndSortAsc_shouldReturnTheCorrectResults(
    client: testing.FlaskClient, ios_scans: models.Scan
) -> None:
    """Test query for multiple scans with pagination and sort ascending."""
    with models.Database() as session:
        scans = session.query(models.Scan).filter(models.Scan.id.in_([1, 2])).all()
        assert scans is not None

    query = """
        query Scans($scanIds: [Int!], $page: Int, $numberElements: Int, $orderBy: OxoScanOrderByEnum, $sort: SortEnum) {
            scans(scanIds: $scanIds, page: $page, numberElements: $numberElements, orderBy: $orderBy, sort: $sort) {
                scans {
                    id
                    title
                    asset
                    progress
                    createdTime
                }
            }
        }
    """

    response = client.post(
        "/graphql",
        json={
            "query": query,
            "variables": {
                "scanIds": [1, 2],
                "page": 1,
                "numberElements": 2,
                "orderBy": "ScanId",
                "sort": "Asc",
            },
        },
    )

    assert response.status_code == 200, response.get_json()
    scan1 = response.get_json()["data"]["scans"]["scans"][0]
    scan2 = response.get_json()["data"]["scans"]["scans"][1]
    assert scan1["id"] == "1"
    assert scan1["title"] == scans[0].title
    assert scan1["asset"] == scans[0].asset
    assert scan1["progress"] == scans[0].progress.name
    assert scan1["createdTime"] == scans[0].created_time.isoformat()
    assert scan2["id"] == "2"
    assert scan2["title"] == scans[1].title
    assert scan2["asset"] == scans[1].asset
    assert scan2["progress"] == scans[1].progress.name
    assert scan2["createdTime"] == scans[1].created_time.isoformat()


def testQueryMultipleScans_whenNoScanIdsSpecified_shouldReturnAllScans(
    client: testing.FlaskClient, ios_scans: models.Scan
) -> None:
    """Test query for multiple scans when no scan ids are specified."""
    with models.Database() as session:
        scans = session.query(models.Scan).all()
        assert scans is not None

    query = """
        query Scans {
            scans {
                scans {
                    id
                    title
                    asset
                    progress
                    createdTime
                }
            }
        }
    """

    response = client.post("/graphql", json={"query": query})

    assert response.status_code == 200, response.get_json()
    scan1 = response.get_json()["data"]["scans"]["scans"][1]
    scan2 = response.get_json()["data"]["scans"]["scans"][0]
    assert scan1["id"] == "1"
    assert scan1["title"] == scans[0].title
    assert scan1["asset"] == scans[0].asset
    assert scan1["progress"] == scans[0].progress.name
    assert scan1["createdTime"] == scans[0].created_time.isoformat()
    assert scan2["id"] == "2"
    assert scan2["title"] == scans[1].title
    assert scan2["asset"] == scans[1].asset
    assert scan2["progress"] == scans[1].progress.name
    assert scan2["createdTime"] == scans[1].created_time.isoformat()


def testQueryMultipleVulnerabilities_always_shouldReturnMultipleVulnerabilities(
    client: testing.FlaskClient, ios_scans: models.Scan
) -> None:
    """Test query for multiple vulnerabilities."""
    with models.Database() as session:
        vulnerabilities = (
            session.query(models.Vulnerability)
            .filter(models.Vulnerability.id.in_([1, 2]))
            .all()
        )
        assert vulnerabilities is not None
    query = """
            query Scans {
                scans {
                    scans {
                        title
                        asset
                        createdTime
                        vulnerabilities {
                            vulnerabilities {
                                technicalDetail
                                detail {
                                    title
                                }
                            }
                        }
                    }
                }
            }
    """

    response = client.post("/graphql", json={"query": query})

    assert response.status_code == 200, response.get_json()
    vulnerability = response.get_json()["data"]["scans"]["scans"][0]["vulnerabilities"][
        "vulnerabilities"
    ][0]
    assert vulnerability["technicalDetail"] == vulnerabilities[1].technical_detail
    assert vulnerability["detail"]["title"] == vulnerabilities[1].title
    vulnerability = response.get_json()["data"]["scans"]["scans"][1]["vulnerabilities"][
        "vulnerabilities"
    ][0]
    assert vulnerability["technicalDetail"] == vulnerabilities[0].technical_detail
    assert vulnerability["detail"]["title"] == vulnerabilities[0].title


def testQueryMultipleKBVulnerabilities_always_shouldReturnMultipleKBVulnerabilities(
    client: testing.FlaskClient, ios_scans: models.Scan
) -> None:
    """Test query for multiple KB vulnerabilities."""
    with models.Database() as session:
        kb_vulnerabilities = (
            session.query(models.Vulnerability)
            .filter(models.Vulnerability.id.in_([1, 2]))
            .all()
        )
        assert kb_vulnerabilities is not None
    query = """
            query Scans {
                scans {
                    scans {
                        title
                        asset
                        createdTime
                        kbVulnerabilities {
                            kb {
                                title
                                shortDescription
                                recommendation
                            }
                        }
                    }
                }
            }
    """

    response = client.post("/graphql", json={"query": query})

    assert response.status_code == 200, response.get_json()
    kb_vulnerability = response.get_json()["data"]["scans"]["scans"][1][
        "kbVulnerabilities"
    ][0]["kb"]
    assert kb_vulnerability["recommendation"] == kb_vulnerabilities[0].recommendation
    assert (
        kb_vulnerability["shortDescription"] == kb_vulnerabilities[0].short_description
    )
    assert kb_vulnerability["title"] == kb_vulnerabilities[0].title
    kb_vulnerability = response.get_json()["data"]["scans"]["scans"][0][
        "kbVulnerabilities"
    ][0]["kb"]
    assert kb_vulnerability["recommendation"] == kb_vulnerabilities[1].recommendation
    assert (
        kb_vulnerability["shortDescription"] == kb_vulnerabilities[1].short_description
    )
    assert kb_vulnerability["title"] == kb_vulnerabilities[1].title


def testQueryMultipleVulnerabilities_always_returnMaxRiskRating(
    client: testing.FlaskClient, android_scan: models.Scan
) -> None:
    """Test query for multiple vulnerabilities with max risk rating."""
    query = """
        query Scans {
            scans {
                scans {
                    title
                    messageStatus
                    progress
                    kbVulnerabilities {
                        highestRiskRating
                        kb {
                            title
                        }
                    }
                }
            }
        }
    """

    response = client.post("/graphql", json={"query": query})

    assert response.status_code == 200, response.get_json()
    max_risk_rating = response.get_json()["data"]["scans"]["scans"][0][
        "kbVulnerabilities"
    ][0]["highestRiskRating"]
    assert max_risk_rating == "CRITICAL"
    max_risk_rating = response.get_json()["data"]["scans"]["scans"][0][
        "kbVulnerabilities"
    ][1]["highestRiskRating"]
    assert max_risk_rating == "LOW"


def testQueryScan_whenScanExists_returnScanInfo(
    client: testing.FlaskClient, android_scan: models.Scan
) -> None:
    """Ensure the scan query returns the correct scan with all its information."""
    query = """
        query Scan ($scanId: Int!){
            scan (scanId: $scanId){
                id
                title
                asset
                createdTime
                messageStatus
                progress
                vulnerabilities {
                    vulnerabilities {
                        id
                        technicalDetail
                        riskRating
                        cvssV3Vector
                        dna
                        detail {
                            title
                            shortDescription
                            description
                            recommendation
                            references
                        }
                        cvssV3BaseScore
                    }
                }
                kbVulnerabilities {
                    highestRiskRating
                    highestCvssV3Vector
                    highestCvssV3BaseScore
                    kb {
                        title
                    }
                }
            }
        }
    """

    response = client.post(
        "/graphql", json={"query": query, "variables": {"scanId": android_scan.id}}
    )

    assert response.status_code == 200, response.get_json()
    scan_data = response.get_json()["data"]["scan"]
    assert scan_data["id"] == str(android_scan.id)
    assert scan_data["title"] == android_scan.title
    assert scan_data["progress"] == "DONE"

    vulnerabilities = scan_data["vulnerabilities"]["vulnerabilities"]
    assert len(vulnerabilities) > 0
    assert vulnerabilities[0]["riskRating"] == "LOW"
    assert vulnerabilities[0]["detail"]["title"] == "XSS"
    assert vulnerabilities[0]["detail"]["description"] == "Cross Site Scripting"


def testQueryScan_whenScanDoesNotExist_returnErrorMessage(
    client: testing.FlaskClient,
) -> None:
    """Ensure the scan query returns an error when the scan does not exist."""
    query = """
        query Scan ($scanId: Int!){
            scan (scanId: $scanId){
                id
            }
        }
    """

    response = client.post(
        "/graphql", json={"query": query, "variables": {"scanId": 42}}
    )

    assert response.status_code == 200, response.get_json()
    assert response.get_json()["errors"][0]["message"] == "Scan not found."


def testDeleteScanMutation_whenScanExist_deleteScanAndVulnz(
    client: testing.FlaskClient, android_scan: models.Scan
) -> None:
    """Ensure the delete scan mutation deletes the scan, its statuses & vulnerabilities."""
    with models.Database() as session:
        nb_scans_before_delete = session.query(models.Scan).count()
        nb_vulnz_before_delete = (
            session.query(models.Vulnerability)
            .filter_by(scan_id=android_scan.id)
            .count()
        )
        nb_status_before_delete = (
            session.query(models.ScanStatus).filter_by(scan_id=android_scan.id).count()
        )

    query = """
        mutation DeleteScan ($scanId: Int!){
            deleteScan (scanId: $scanId) {
                result
            }
        }
    """

    response = client.post(
        "/graphql", json={"query": query, "variables": {"scanId": android_scan.id}}
    )

    assert response.status_code == 200, response.get_json()
    assert nb_scans_before_delete > 0
    assert nb_vulnz_before_delete > 0
    assert nb_status_before_delete > 0
    with models.Database() as session:
        assert session.query(models.Scan).count() == 0
        assert (
            session.query(models.Vulnerability)
            .filter_by(scan_id=android_scan.id)
            .count()
            == 0
        )
        assert (
            session.query(models.ScanStatus).filter_by(scan_id=android_scan.id).count()
            == 0
        )


def testDeleteScanMutation_whenScanDoesNotExist_returnErrorMessage(
    client: testing.FlaskClient,
) -> None:
    """Ensure the delete scan mutation returns an error message when the scan does not exist."""
    query = """
        mutation DeleteScan ($scanId: Int!){
            deleteScan (scanId: $scanId) {
                result
            }
        }
    """

    response = client.post(
        "/graphql", json={"query": query, "variables": {"scanId": 42}}
    )

    assert response.status_code == 200, response.get_json()
    assert response.get_json()["errors"][0]["message"] == "Scan not found."


def testStopScanMutation_always_shouldStopScan(
    client: testing.FlaskClient, in_progress_web_scan: None
) -> None:
    """Test stopScan mutation when scan is running should stop scan."""
    with models.Database() as session:
        nbr_scans_before_import = session.query(models.Scan).count()
        scan = session.query(models.Scan).first()
        scan_progress = scan.progress

        query = """
            mutation stopScan($scanId: String!){
  stopScan(scanId: $scanId){
    scan{
      id
    }
  }
}
        """
        response = client.post(
            "/graphql", json={"query": query, "variables": {"scanId": str(scan.id)}}
        )

        assert response.status_code == 200, response.content
        session.refresh(scan)
        scan = session.query(models.Scan).first()
        response_json = response.get_json()
        nbr_scans_after_import = session.query(models.Scan).count()
        assert response_json["data"] == {"stopScan": {"scan": {"id": "1"}}}
        assert nbr_scans_before_import == 1
        assert scan.progress == models.ScanProgress.STOPPED
        assert scan.progress != scan_progress
        assert nbr_scans_after_import == nbr_scans_before_import


def testStopScanMutation_whenNoScanFound_shouldReturnError(
    client: testing.FlaskClient,
) -> None:
    """Test stopScan mutation when scan doesn't exist should return error message."""
    query = """
        mutation stopScan($scanId: String!){
stopScan(scanId: $scanId){
scan{
  id
}
}
}
    """
    response = client.post(
        "/graphql", json={"query": query, "variables": {"scanId": "5"}}
    )

    assert response.status_code == 200, response.content
    response_json = response.get_json()
    assert response_json["errors"][0]["message"] == "Scan not found."
