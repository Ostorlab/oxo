"""Unit tests for the oxo module."""

import io
import json

import flask

from ostorlab.runtimes.local.models import models


def testImportScanMutation_always_shouldImportScan(
    client: flask.testing.FlaskClient, zip_file_bytes: bytes
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

        assert response.status_code == 200
        response_json = response.get_json()
        nbr_scans_after_import = session.query(models.Scan).count()
        assert (
            response_json["data"]["importScan"]["message"]
            == "Scan imported successfully"
        )
        assert nbr_scans_after_import == nbr_scans_before_import + 1


def testQuerySingleScan_always_shouldReturnSingleScan(
    client: flask.testing.FlaskClient, web_scan: models.Scan
) -> None:
    """Test query for single scan."""
    with models.Database() as session:
        scan = session.query(models.Scan).filter_by(id=1).first()
        assert scan is not None

    query = """
        query Scan($id: Int!) {
            scan(id: $id) {
                id
                title
                asset
                progress
                createdTime
            }
        }
    """

    response = client.post("/graphql", json={"query": query, "variables": {"id": 1}})

    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json["data"]["scan"]["id"] == 1
    assert response_json["data"]["scan"]["title"] == scan.title
    assert response_json["data"]["scan"]["asset"] == scan.asset
    assert response_json["data"]["scan"]["progress"] == str(scan.progress)
    assert response_json["data"]["scan"]["createdTime"] == scan.created_time.isoformat()


def testQuerySingleVulnerability_always_shouldReturnSingleVulnerability(
    client: flask.testing.FlaskClient, web_scan: models.Scan
) -> None:
    """Test query for single vulnerability."""
    with models.Database() as session:
        vulnerability = session.query(models.Vulnerability).filter_by(id=1).first()
        assert vulnerability is not None

    query = """
        query Vulnerability($id: Int!) {
            vulnerability(id: $id) {
                id
                technicalDetail
                riskRating
                cvssV3Vector
                dna
                title
                shortDescription
                description
                recommendation
                references
                location
            }
        }
    """

    response = client.post("/graphql", json={"query": query, "variables": {"id": 1}})

    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json["data"]["vulnerability"]["id"] == 1
    assert (
        response_json["data"]["vulnerability"]["technicalDetail"]
        == vulnerability.technical_detail
    )
    assert response_json["data"]["vulnerability"]["riskRating"] == str(
        vulnerability.risk_rating
    )
    assert (
        response_json["data"]["vulnerability"]["cvssV3Vector"]
        == vulnerability.cvss_v3_vector
    )
    assert response_json["data"]["vulnerability"]["dna"] == vulnerability.dna
    assert response_json["data"]["vulnerability"]["title"] == vulnerability.title
    assert (
        response_json["data"]["vulnerability"]["shortDescription"]
        == vulnerability.short_description
    )
    assert (
        response_json["data"]["vulnerability"]["description"]
        == vulnerability.description
    )
    assert (
        response_json["data"]["vulnerability"]["recommendation"]
        == vulnerability.recommendation
    )
    assert (
        response_json["data"]["vulnerability"]["references"] == vulnerability.references
    )
    assert response_json["data"]["vulnerability"]["location"] == vulnerability.location


def testQueryMultipleScans_always_shouldReturnMultipleScans(
    client: flask.testing.FlaskClient, ios_scans: models.Scan
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

    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json["data"]["scans"]["scans"][0]["id"] == 2
    assert response_json["data"]["scans"]["scans"][0]["title"] == scans[1].title
    assert response_json["data"]["scans"]["scans"][0]["asset"] == scans[1].asset
    assert response_json["data"]["scans"]["scans"][0]["progress"] == str(
        scans[1].progress
    )
    assert (
        response_json["data"]["scans"]["scans"][0]["createdTime"]
        == scans[1].created_time.isoformat()
    )
    assert response_json["data"]["scans"]["scans"][1]["id"] == 1
    assert response_json["data"]["scans"]["scans"][1]["title"] == scans[0].title
    assert response_json["data"]["scans"]["scans"][1]["asset"] == scans[0].asset
    assert response_json["data"]["scans"]["scans"][1]["progress"] == str(
        scans[0].progress
    )
    assert (
        response_json["data"]["scans"]["scans"][1]["createdTime"]
        == scans[0].created_time.isoformat()
    )


def testQueryMultipleVulnerabilities_always_shouldReturnMultipleVulnerabilities(
    client: flask.testing.FlaskClient, ios_scans: models.Scan
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
        query Vulnerabilities($vulnerabilityIds: [Int!]) {
            vulnerabilities(vulnerabilityIds: $vulnerabilityIds) {
                vulnerabilities {
                    id
                    technicalDetail
                    riskRating
                    cvssV3Vector
                    dna
                    title
                    shortDescription
                    description
                    recommendation
                    references
                    location
                }
            }
        }
    """

    response = client.post(
        "/graphql", json={"query": query, "variables": {"vulnerabilityIds": [1, 2]}}
    )

    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json["data"]["vulnerabilities"]["vulnerabilities"][0]["id"] == 2
    assert (
        response_json["data"]["vulnerabilities"]["vulnerabilities"][0][
            "technicalDetail"
        ]
        == vulnerabilities[1].technical_detail
    )
    assert response_json["data"]["vulnerabilities"]["vulnerabilities"][0][
        "riskRating"
    ] == str(vulnerabilities[1].risk_rating)
    assert (
        response_json["data"]["vulnerabilities"]["vulnerabilities"][0]["cvssV3Vector"]
        == vulnerabilities[1].cvss_v3_vector
    )
    assert (
        response_json["data"]["vulnerabilities"]["vulnerabilities"][0]["dna"]
        == vulnerabilities[1].dna
    )
    assert (
        response_json["data"]["vulnerabilities"]["vulnerabilities"][0]["title"]
        == vulnerabilities[1].title
    )
    assert (
        response_json["data"]["vulnerabilities"]["vulnerabilities"][0][
            "shortDescription"
        ]
        == vulnerabilities[1].short_description
    )
    assert (
        response_json["data"]["vulnerabilities"]["vulnerabilities"][0]["description"]
        == vulnerabilities[1].description
    )
    assert (
        response_json["data"]["vulnerabilities"]["vulnerabilities"][0]["recommendation"]
        == vulnerabilities[1].recommendation
    )
    assert (
        response_json["data"]["vulnerabilities"]["vulnerabilities"][0]["references"]
        == vulnerabilities[1].references
    )
    assert (
        response_json["data"]["vulnerabilities"]["vulnerabilities"][0]["location"]
        == vulnerabilities[1].location
    )
    assert response_json["data"]["vulnerabilities"]["vulnerabilities"][1]["id"] == 1
    assert (
        response_json["data"]["vulnerabilities"]["vulnerabilities"][1][
            "technicalDetail"
        ]
        == vulnerabilities[0].technical_detail
    )
    assert response_json["data"]["vulnerabilities"]["vulnerabilities"][1][
        "riskRating"
    ] == str(vulnerabilities[0].risk_rating)
    assert (
        response_json["data"]["vulnerabilities"]["vulnerabilities"][1]["cvssV3Vector"]
        == vulnerabilities[0].cvss_v3_vector
    )
    assert (
        response_json["data"]["vulnerabilities"]["vulnerabilities"][1]["dna"]
        == vulnerabilities[0].dna
    )
    assert (
        response_json["data"]["vulnerabilities"]["vulnerabilities"][1]["title"]
        == vulnerabilities[0].title
    )
    assert (
        response_json["data"]["vulnerabilities"]["vulnerabilities"][1][
            "shortDescription"
        ]
        == vulnerabilities[0].short_description
    )
    assert (
        response_json["data"]["vulnerabilities"]["vulnerabilities"][1]["description"]
        == vulnerabilities[0].description
    )
    assert (
        response_json["data"]["vulnerabilities"]["vulnerabilities"][1]["recommendation"]
        == vulnerabilities[0].recommendation
    )
    assert (
        response_json["data"]["vulnerabilities"]["vulnerabilities"][1]["references"]
        == vulnerabilities[0].references
    )
    assert (
        response_json["data"]["vulnerabilities"]["vulnerabilities"][1]["location"]
        == vulnerabilities[0].location
    )
