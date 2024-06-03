"""Unit tests for the oxo module."""

import io
import json
import pathlib

import pytest
from docker.models import services as services_model
import ubjson
from flask import testing
from pytest_mock import plugin

from ostorlab.runtimes.local.models import models


def testImportScanMutation_always_shouldImportScan(
    authenticated_flask_client: testing.FlaskClient, zip_file_bytes: bytes
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

        response = authenticated_flask_client.post(
            "/graphql", data=data, content_type="multipart/form-data"
        )

        assert response.status_code == 200, response.get_json()
        response_json = response.get_json()
        nbr_scans_after_import = session.query(models.Scan).count()
        assert (
            response_json["data"]["importScan"]["message"]
            == "Scan imported successfully"
        )
        assert nbr_scans_after_import == nbr_scans_before_import + 1


def testQueryMultipleScans_always_shouldReturnMultipleScans(
    authenticated_flask_client: testing.FlaskClient, ios_scans: models.Scan
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

    response = authenticated_flask_client.post(
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
    authenticated_flask_client: testing.FlaskClient, ios_scans: models.Scan
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

    response = authenticated_flask_client.post(
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
    authenticated_flask_client: testing.FlaskClient, ios_scans: models.Scan
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

    response = authenticated_flask_client.post("/graphql", json={"query": query})

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
    authenticated_flask_client: testing.FlaskClient, ios_scans: models.Scan
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

    response = authenticated_flask_client.post("/graphql", json={"query": query})

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
    authenticated_flask_client: testing.FlaskClient, ios_scans: models.Scan
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
                                references {
                                    title
                                    url
                                }
                            }
                        }
                    }
                }
            }
    """

    response = authenticated_flask_client.post("/graphql", json={"query": query})

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
    assert (
        kb_vulnerability["references"][0]["title"]
        == "C++ Core Guidelines R.10 - Avoid malloc() and free()"
    )
    assert (
        kb_vulnerability["references"][0]["url"]
        == "https://github.com/isocpp/CppCoreGuidelines/blob/036324/CppCoreGuidelines.md#r10-avoid-malloc-and-free"
    )


def testQueryMultipleVulnerabilities_always_returnMaxRiskRating(
    authenticated_flask_client: testing.FlaskClient, android_scan: models.Scan
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

    response = authenticated_flask_client.post("/graphql", json={"query": query})

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
    authenticated_flask_client: testing.FlaskClient, android_scan: models.Scan
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

    response = authenticated_flask_client.post(
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
    authenticated_flask_client: testing.FlaskClient,
) -> None:
    """Ensure the scan query returns an error when the scan does not exist."""
    query = """
        query Scan ($scanId: Int!){
            scan (scanId: $scanId){
                id
            }
        }
    """

    response = authenticated_flask_client.post(
        "/graphql", json={"query": query, "variables": {"scanId": 42}}
    )

    assert response.status_code == 200, response.get_json()
    assert response.get_json()["errors"][0]["message"] == "Scan not found."


def testDeleteScanMutation_whenScanExist_deleteScanAndVulnz(
    authenticated_flask_client: testing.FlaskClient, android_scan: models.Scan
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

    response = authenticated_flask_client.post(
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
    authenticated_flask_client: testing.FlaskClient,
) -> None:
    """Ensure the delete scan mutation returns an error message when the scan does not exist."""
    query = """
        mutation DeleteScan ($scanId: Int!){
            deleteScan (scanId: $scanId) {
                result
            }
        }
    """

    response = authenticated_flask_client.post(
        "/graphql", json={"query": query, "variables": {"scanId": 42}}
    )

    assert response.status_code == 200, response.get_json()
    assert response.get_json()["errors"][0]["message"] == "Scan not found."


def testScansQuery_withPagination_shouldReturnPageInfo(
    authenticated_flask_client: testing.FlaskClient,
    ios_scans: models.Scan,
    web_scan: models.Scan,
) -> None:
    """Test the scan query with pagination, should return the correct pageInfo."""

    with models.Database() as session:
        scans = session.query(models.Scan).all()
        assert scans is not None

    query = """query Scans($scanIds: [Int!], $page: Int, $numberElements: Int) {
  scans(scanIds: $scanIds, page: $page, numberElements: $numberElements) {
    pageInfo{
      count
      numPages
      hasNext
      hasPrevious
    }
    scans {
      id
    }
  }
}
"""

    response = authenticated_flask_client.post(
        "/graphql", json={"query": query, "variables": {"page": 1, "numberElements": 2}}
    )

    assert response.status_code == 200, response.get_json()
    assert response.get_json()["data"]["scans"]["pageInfo"] == {
        "count": 3,
        "hasNext": True,
        "hasPrevious": False,
        "numPages": 2,
    }


def testVulnerabilitiesQuery_withPagination_shouldReturnPageInfo(
    authenticated_flask_client: testing.FlaskClient,
    android_scan: models.Scan,
) -> None:
    """Test the vulnerabilities query with pagination, should return the correct pageInfo."""

    with models.Database() as session:
        vulnerabilities = session.query(models.Vulnerability).all()
        assert vulnerabilities is not None

    query = """query Scans($scanIds: [Int!], $scanPage: Int, $scanElements: Int, $vulnPage: Int, $vulnElements: Int) {
        scans(scanIds: $scanIds, page: $scanPage, numberElements: $scanElements) {
            pageInfo {
                count
                numPages
                hasNext
                hasPrevious
            }
            scans {
                id
                title
                vulnerabilities(page: $vulnPage, numberElements: $vulnElements) {
                    pageInfo {
                        count
                        numPages
                        hasNext
                        hasPrevious
                    }
                    vulnerabilities {
                        id
                    }
                }
            }
        }
    }
    """

    response = authenticated_flask_client.post(
        "/graphql",
        json={
            "query": query,
            "variables": {
                "scanPage": 1,
                "scanElements": 1,
                "vulnPage": 2,
                "vulnElements": 1,
            },
        },
    )

    assert response.status_code == 200, response.get_json()
    assert response.get_json()["data"]["scans"]["scans"][0]["vulnerabilities"][
        "pageInfo"
    ] == {
        "count": 4,
        "hasNext": True,
        "hasPrevious": True,
        "numPages": 4,
    }


def testQueryAllAgentGroups_always_shouldReturnAllAgentGroups(
    authenticated_flask_client: testing.FlaskClient, agent_groups: models.AgentGroup
) -> None:
    """Test query for multiple agent groups."""
    with models.Database() as session:
        agent_groups = (
            session.query(models.AgentGroup)
            .filter(models.AgentGroup.id.in_([1, 2]))
            .all()
        )
        assert agent_groups is not None

    query = """
            query AgentGroups ($orderBy: AgentGroupOrderByEnum, $sort: SortEnum){
                agentGroups (orderBy: $orderBy, sort: $sort) {
                    agentGroups {
                        id
                        name
                        description
                        createdTime
                        key
                        agents {
                            agents {
                                id
                                key
                                args {
                                    args {
                                        id
                                        name
                                        type
                                        description
                                        value
                                    }
                                }
                            }
                        }
                    }
                }
            }
    """
    variables = {"orderBy": "AgentGroupId", "sort": "Asc"}
    ubjson_data = ubjson.dumpb({"query": query, "variables": variables})

    response = authenticated_flask_client.post(
        "/graphql", data=ubjson_data, headers={"Content-Type": "application/ubjson"}
    )

    assert response.status_code == 200, ubjson.loadb(response.data)
    agent_groups_data = ubjson.loadb(response.data)["data"]["agentGroups"][
        "agentGroups"
    ]
    assert len(agent_groups_data) == 2
    agent_group1 = agent_groups_data[0]
    agent_group2 = agent_groups_data[1]
    assert agent_group1["name"] == agent_groups[0].name
    assert agent_group1["description"] == agent_groups[0].description
    assert agent_group1["key"] == f"agentgroup//{agent_groups[0].name}"
    assert agent_group1["createdTime"] == agent_groups[0].created_time.isoformat()
    assert agent_group2["name"] == agent_groups[1].name
    assert agent_group2["description"] == agent_groups[1].description
    assert agent_group2["key"] == f"agentgroup//{agent_groups[1].name}"
    assert agent_group2["createdTime"] == agent_groups[1].created_time.isoformat()
    agent_group1_agents = agent_group1["agents"]["agents"]
    agent_group2_agents = agent_group2["agents"]["agents"]
    assert len(agent_group1_agents) == 2
    assert len(agent_group2_agents) == 1
    assert agent_group1_agents[0]["key"] == "agent/ostorlab/agent1"
    assert agent_group1_agents[1]["key"] == "agent/ostorlab/agent2"
    assert agent_group2_agents[0]["key"] == "agent/ostorlab/agent1"
    agent1_args = agent_group1_agents[0]["args"]["args"]
    agent2_args = agent_group1_agents[1]["args"]["args"]
    assert len(agent1_args) == 1
    assert len(agent2_args) == 1
    assert agent1_args[0]["name"] == "arg1"
    assert agent1_args[0]["type"] == "number"
    assert agent1_args[0]["value"] == b"42"
    assert agent2_args[0]["name"] == "arg2"
    assert agent2_args[0]["type"] == "string"
    assert agent2_args[0]["value"] == b"hello"


def testQuerySingleAgentGroup_always_shouldReturnSingleAgentGroup(
    authenticated_flask_client: testing.FlaskClient, agent_groups: models.AgentGroup
) -> None:
    """Test query for a single agent group."""
    with models.Database() as session:
        agent_group = session.query(models.AgentGroup).filter_by(id=1).first()
        assert agent_group is not None

    query = """
            query AgentGroup ($agentGroupIds: [Int!]){
                agentGroups (agentGroupIds: $agentGroupIds) {
                    agentGroups {
                        id
                        name
                        description
                        createdTime
                        key
                        agents {
                            agents {
                                id
                                key
                                args {
                                    args {
                                        id
                                        name
                                        type
                                        description
                                        value
                                    }
                                }
                            }
                        }
                    }
                }
            }
    """
    variables = {"agentGroupIds": [1]}
    ubjson_data = ubjson.dumpb({"query": query, "variables": variables})

    response = authenticated_flask_client.post(
        "/graphql", data=ubjson_data, headers={"Content-Type": "application/ubjson"}
    )

    assert response.status_code == 200, ubjson.loadb(response.data)
    agent_groups_data = ubjson.loadb(response.data)["data"]["agentGroups"][
        "agentGroups"
    ]
    assert len(agent_groups_data) == 1
    agent_group_data = agent_groups_data[0]
    assert agent_group_data["name"] == agent_group.name
    assert agent_group_data["description"] == agent_group.description
    assert agent_group_data["key"] == f"agentgroup//{agent_group.name}"
    assert agent_group_data["createdTime"] == agent_group.created_time.isoformat()
    agent_group_agents = agent_group_data["agents"]["agents"]
    assert len(agent_group_agents) == 2
    assert agent_group_agents[0]["key"] == "agent/ostorlab/agent1"
    assert agent_group_agents[1]["key"] == "agent/ostorlab/agent2"
    agent1_args = agent_group_agents[0]["args"]["args"]
    agent2_args = agent_group_agents[1]["args"]["args"]
    assert len(agent1_args) == 1
    assert len(agent2_args) == 1
    assert agent1_args[0]["name"] == "arg1"
    assert agent1_args[0]["type"] == "number"
    assert agent1_args[0]["value"] == b"42"
    assert agent2_args[0]["name"] == "arg2"
    assert agent2_args[0]["type"] == "string"
    assert agent2_args[0]["value"] == b"hello"


def testQueryAgentGroupsWithPagination_always_returnPageInfo(
    authenticated_flask_client: testing.FlaskClient, agent_groups: models.AgentGroup
) -> None:
    """Test query for agent groups with pagination."""
    with models.Database() as session:
        agent_groups = session.query(models.AgentGroup).all()
        assert agent_groups is not None

    query = """
            query AgentGroups ($page: Int, $numberElements: Int, $orderBy: AgentGroupOrderByEnum, $sort: SortEnum){
                agentGroups (page: $page, numberElements: $numberElements, orderBy: $orderBy, sort: $sort) {
                    agentGroups {
                        id
                        name
                        description
                        createdTime
                        key
                        agents {
                            agents {
                                id
                                key
                                args {
                                    args {
                                        id
                                        name
                                        type
                                        description
                                        value
                                    }
                                }
                            }
                        }
                    }
                    pageInfo {
                        count
                        numPages
                        hasPrevious
                        hasNext
                    }
                }
            }
    """
    variables = {
        "page": 2,
        "numberElements": 1,
        "orderBy": "AgentGroupId",
        "sort": "Asc",
    }
    ubjson_data = ubjson.dumpb({"query": query, "variables": variables})

    response = authenticated_flask_client.post(
        "/graphql",
        data=ubjson_data,
        headers={"Content-Type": "application/ubjson"},
    )

    assert response.status_code == 200, ubjson.loadb(response.data)
    response_data = ubjson.loadb(response.data)["data"]["agentGroups"]
    agent_groups_data = response_data["agentGroups"]
    page_info = response_data["pageInfo"]
    assert len(agent_groups_data) == 1
    ag = agent_groups_data[0]
    assert ag["name"] == agent_groups[1].name
    assert ag["description"] == agent_groups[1].description
    assert ag["key"] == f"agentgroup//{agent_groups[1].name}"
    assert ag["createdTime"] == agent_groups[1].created_time.isoformat()
    assert page_info["count"] == 2
    assert page_info["numPages"] == 2
    assert page_info["hasPrevious"] is True
    assert page_info["hasNext"] is False


def testQueryMultipleScans_whenApiKeyIsInvalid_returnUnauthorized(
    unauthenticated_flask_client: testing.FlaskClient, ios_scans: models.Scan
) -> None:
    """Test query for multiple scans when the API key is invalid."""
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

    response = unauthenticated_flask_client.post(
        "/graphql", json={"query": query}, headers={"X-API-KEY": "invalid"}
    )

    assert response.status_code == 401
    assert response.get_json()["error"] == "Unauthorized"


def testCreateAsset_androidStore_createsNewAsset(
    authenticated_flask_client: testing.FlaskClient, clean_db: None
) -> None:
    """Ensure the android store asset is created successfully through the createAsset API."""
    del clean_db
    query = """
        mutation createAndroidStore($assets: [AssetInputType]!) {
            createAsset(assets: $assets) {
                assets {
                    ... on AndroidStoreAssetType {
                        id
                        packageName
                        applicationName
                    }
                }
            }
        }
    """

    resp = authenticated_flask_client.post(
        "/graphql",
        json={
            "query": query,
            "variables": {
                "assets": [
                    {
                        "androidStore": {
                            "applicationName": "fake_app",
                            "packageName": "a.b.c",
                        }
                    }
                ]
            },
        },
    )

    assert resp.status_code == 200, resp.get_json()
    asset_data = resp.get_json()["data"]["createAsset"]["assets"][0]
    assert asset_data["id"] is not None
    assert asset_data["packageName"] == "a.b.c"
    assert asset_data["applicationName"] == "fake_app"
    with models.Database() as session:
        assert session.query(models.AndroidStore).count() == 1
        assert session.query(models.AndroidStore).all()[0].package_name == "a.b.c"
        assert (
            session.query(models.AndroidStore).all()[0].application_name == "fake_app"
        )


def testCreateAsset_iOSStore_createsNewAsset(
    authenticated_flask_client: testing.FlaskClient, clean_db: None
) -> None:
    """Ensure the ios store asset is created successfully through the createAsset API."""
    del clean_db
    query = """
        mutation createiOSStore($assets: [AssetInputType]!) {
            createAsset(assets: $assets) {
                assets {
                    ... on IOSStoreAssetType {
                        id
                        bundleId
                        applicationName
                        scans {
                            id
                            title                            
                        }
                    }
                }
            }
        }
    """

    resp = authenticated_flask_client.post(
        "/graphql",
        json={
            "query": query,
            "variables": {
                "assets": [
                    {
                        "iosStore": {
                            "applicationName": "fake_app",
                            "bundleId": "a.b.c",
                        }
                    }
                ]
            },
        },
    )

    assert resp.status_code == 200, resp.get_json()
    asset_data = resp.get_json()["data"]["createAsset"]["assets"][0]
    assert asset_data["id"] is not None
    assert asset_data["bundleId"] == "a.b.c"
    assert asset_data["applicationName"] == "fake_app"
    with models.Database() as session:
        assert session.query(models.IosStore).count() == 1
        assert session.query(models.IosStore).all()[0].bundle_id == "a.b.c"
        assert session.query(models.IosStore).all()[0].application_name == "fake_app"


def testCreateAsset_url_createsNewAsset(
    authenticated_flask_client: testing.FlaskClient, clean_db: None
) -> None:
    """Ensure the url asset & its links are created successfully through the createAsset API."""
    del clean_db
    query = """
        mutation createUrl($assets: [AssetInputType]!) {
            createAsset(assets: $assets) {
                assets {
                    ... on UrlAssetType {
                        id
                        links
                    }
                }
            }
        }
    """

    resp = authenticated_flask_client.post(
        "/graphql",
        json={
            "query": query,
            "variables": {
                "assets": [
                    {
                        "url": {
                            "links": [
                                "https://www.example.com",
                                "https://www.example2.com",
                            ],
                        }
                    }
                ]
            },
        },
    )

    assert resp.status_code == 200, resp.get_json()
    asset_data = resp.get_json()["data"]["createAsset"]["assets"][0]
    assert asset_data["id"] is not None
    assert asset_data["links"] == [
        "https://www.example.com",
        "https://www.example2.com",
    ]
    with models.Database() as session:
        assert session.query(models.Url).count() == 1
        assert json.loads(session.query(models.Url).all()[0].links) == [
            "https://www.example.com",
            "https://www.example2.com",
        ]


def testCreateAsset_network_createsNewAsset(
    authenticated_flask_client: testing.FlaskClient, clean_db: None
) -> None:
    """Ensure the network asset & its ips are created successfully through the createAsset API."""
    del clean_db
    query = """
        mutation createNetwork($assets: [AssetInputType]!) {
            createAsset(assets: $assets) {
                assets {
                    ... on NetworkAssetType {
                        id
                        networks
                    }
                }
            }
        }
    """

    resp = authenticated_flask_client.post(
        "/graphql",
        json={
            "query": query,
            "variables": {
                "assets": [
                    {
                        "network": {
                            "networks": ["8.8.8.8/24", "42.42.42.42"],
                        }
                    }
                ]
            },
        },
    )

    assert resp.status_code == 200, resp.get_json()
    asset_data = resp.get_json()["data"]["createAsset"]["assets"][0]
    assert asset_data["id"] is not None
    assert asset_data["networks"] == ["8.8.8.8/24", "42.42.42.42"]
    with models.Database() as session:
        assert session.query(models.Network).count() == 1
        assert json.loads(session.query(models.Network).all()[0].networks) == [
            "8.8.8.8/24",
            "42.42.42.42",
        ]


def testCreateAsset_androidFile_createsNewAsset(
    authenticated_flask_client: testing.FlaskClient, clean_db: None
) -> None:
    """Ensure the android file is created successfully through the createAsset API."""
    del clean_db
    query = """
        mutation createAndroidFile($assets: [AssetInputType]!) {
            createAsset(assets: $assets) {
                assets {
                    ... on AndroidFileAssetType {
                        id
                        packageName
                        path
                    }
                }
            }
        }
    """
    apk_path = pathlib.Path(__file__).parent.parent / "files" / "android.apk"
    data = {
        "operations": json.dumps(
            {
                "query": query,
                "variables": {
                    "assets": [
                        {
                            "androidFile": {
                                "file": None,
                                "packageName": "a.b.c",
                            }
                        }
                    ]
                },
            }
        ),
        "0": apk_path.open("rb"),
        "map": json.dumps({"0": ["variables.assets.0.androidFile.file"]}),
    }

    resp = authenticated_flask_client.post(
        "/graphql",
        data=data,
    )

    assert resp.status_code == 200, resp.get_json()
    asset_data = resp.get_json()["data"]["createAsset"]["assets"][0]
    assert asset_data["id"] is not None
    assert asset_data["packageName"] == "a.b.c"
    assert ".ostorlab/uploads/android_" in asset_data["path"]
    with models.Database() as session:
        assert session.query(models.AndroidFile).count() == 1
        assert session.query(models.AndroidFile).all()[0].package_name == "a.b.c"
        assert (
            ".ostorlab/uploads/android_"
            in session.query(models.AndroidFile).all()[0].path
        )


def testCreateAsset_iOSFile_createsNewAsset(
    authenticated_flask_client: testing.FlaskClient, clean_db: None
) -> None:
    """Ensure the iOS file is created successfully through the createAsset API."""
    del clean_db
    query = """
        mutation createAndroidFile($assets: [AssetInputType]!) {
            createAsset(assets: $assets) {
                assets {
                    ... on IOSFileAssetType {
                        id
                        bundleId
                        path
                    }
                }
            }
        }
    """
    apk_path = pathlib.Path(__file__).parent.parent / "files" / "ios.ipa"
    data = {
        "operations": json.dumps(
            {
                "query": query,
                "variables": {
                    "assets": [
                        {
                            "iosFile": {
                                "file": None,
                                "bundleId": "a.b.c",
                            }
                        }
                    ]
                },
            }
        ),
        "0": apk_path.open("rb"),
        "map": json.dumps({"0": ["variables.assets.0.iosFile.file"]}),
    }

    resp = authenticated_flask_client.post(
        "/graphql",
        data=data,
    )

    assert resp.status_code == 200, resp.get_json()
    asset_data = resp.get_json()["data"]["createAsset"]["assets"][0]
    assert asset_data["id"] is not None
    assert asset_data["bundleId"] == "a.b.c"
    assert ".ostorlab/uploads/ios_" in asset_data["path"]
    with models.Database() as session:
        assert session.query(models.IosFile).count() == 1
        assert session.query(models.IosFile).all()[0].bundle_id == "a.b.c"
        assert ".ostorlab/uploads/ios_" in session.query(models.IosFile).all()[0].path


def testCreateAsset_whenMultipleAssets_shouldCreateAll(
    authenticated_flask_client: testing.FlaskClient, clean_db: None
) -> None:
    """Ensure the create asset mutation creates all the provided assets assuming, they are independently valid."""
    del clean_db
    query = """
        mutation createAsset($assets: [AssetInputType]!) {
            createAsset(assets: $assets) {
                assets {
                    ... on AndroidStoreAssetType {
                        id
                        packageName
                        applicationName
                    }
                    ... on IOSStoreAssetType {
                        id
                        bundleId
                        applicationName
                    }
                }
            }
        }
    """

    resp = authenticated_flask_client.post(
        "/graphql",
        json={
            "query": query,
            "variables": {
                "assets": [
                    {
                        "androidStore": {
                            "applicationName": "fake_app",
                            "packageName": "a.b.c",
                        }
                    },
                    {
                        "iosStore": {
                            "applicationName": "fake_app",
                            "bundleId": "a.b.c",
                        }
                    },
                ]
            },
        },
    )

    assert resp.status_code == 200, resp.get_json()
    assets_data = resp.get_json()["data"]["createAsset"]["assets"]
    assert assets_data[0]["id"] is not None
    assert assets_data[0]["applicationName"] == "fake_app"
    assert assets_data[0]["packageName"] == "a.b.c"
    assert assets_data[1]["id"] is not None
    assert assets_data[1]["applicationName"] == "fake_app"
    assert assets_data[1]["bundleId"] == "a.b.c"
    with models.Database() as session:
        assert session.query(models.AndroidStore).count() == 1
        assert session.query(models.AndroidStore).all()[0].package_name == "a.b.c"
        assert (
            session.query(models.AndroidStore).all()[0].application_name == "fake_app"
        )
        assert session.query(models.IosStore).count() == 1
        assert session.query(models.IosStore).all()[0].bundle_id == "a.b.c"
        assert session.query(models.IosStore).all()[0].application_name == "fake_app"


def testCreateAsset_whenMultipleTargetsForSameAsset_shouldReturnError(
    authenticated_flask_client: testing.FlaskClient, clean_db: None
) -> None:
    """Ensure the create asset mutation returns an error message when provided with multiple assets."""
    del clean_db
    query = """
        mutation createAsset($assets: [AssetInputType]!) {
            createAsset(assets: $assets) {
                assets {
                    ... on AndroidStoreAssetType {
                        id
                        packageName
                        applicationName
                    }
                    ... on IOSStoreAssetType {
                        id
                        bundleId
                        applicationName
                    }
                }
            }
        }
    """

    resp = authenticated_flask_client.post(
        "/graphql",
        json={
            "query": query,
            "variables": {
                "assets": [
                    {
                        "androidStore": {
                            "applicationName": "fake_app",
                            "packageName": "a.b.c",
                        },
                        "iosStore": {
                            "applicationName": "fake_app",
                            "bundleId": "a.b.c",
                        },
                    }
                ]
            },
        },
    )

    assert resp.status_code == 200, resp.get_json()
    assert "errors" in resp.get_json()
    assert (
        "Invalid assets: Single target input must be defined for asset"
        in resp.get_json()["errors"][0]["message"]
    )


def testCreateAsset_whenNoAsset_shouldReturnError(
    authenticated_flask_client: testing.FlaskClient, clean_db: None
) -> None:
    """Ensure the create asset mutation returns an error message when not asset is provided."""
    del clean_db
    query = """
        mutation createAsset($assets: [AssetInputType]!) {
            createAsset(assets: $assets) {
                assets {
                    ... on AndroidStoreAssetType {
                        id
                        packageName
                        applicationName
                    }
                }
            }
        }
    """

    resp = authenticated_flask_client.post(
        "/graphql",
        json={
            "query": query,
            "variables": {"assets": [{}]},
        },
    )

    assert resp.status_code == 200, resp.get_json()
    assert "errors" in resp.get_json()
    assert (
        "Invalid assets: Asset {} input is missing target."
        == resp.get_json()["errors"][0]["message"]
    )


def testQueryScan_whenAsset_shouldReturnScanAndAssetInformation(
    authenticated_flask_client: testing.FlaskClient,
) -> None:
    """Ensure we can query the specific asset information (depending on the target type) from the scan."""
    with models.Database() as session:
        asset = models.AndroidStore.create(
            package_name="a.b.c", application_name="fake_app"
        )
        session.add(asset)
        session.commit()
        scan = models.Scan(
            title="iOS Scan",
            progress=models.ScanProgress.NOT_STARTED,
            asset_instance=asset,
            asset_id=asset.id,
        )
        session.add(asset)
        session.commit()

    query = """
        query Scans($scanIds: [Int!]) {
            scans(scanIds: $scanIds) {
                scans {
                    id
                    title
                    asset
                    progress
                    createdTime
                    assetInstance {
                        ... on AndroidStoreAssetType {
                            id
                            packageName
                            applicationName
                        }
                    }
                }
            }
        }
    """

    response = authenticated_flask_client.post(
        "/graphql",
        json={"query": query, "variables": {"scanIds": [scan.id]}},
    )
    assert response.status_code == 200, response.get_json()
    scan_data = response.get_json()["data"]["scans"]["scans"][0]
    assert scan_data["title"] == "iOS Scan"
    assert scan_data["assetInstance"]["packageName"] == asset.package_name
    assert scan_data["assetInstance"]["applicationName"] == asset.application_name


def testQueryAsset_whenHasScan_shouldReturnScanInformationFromAssetObject(
    authenticated_flask_client: testing.FlaskClient,
) -> None:
    """Ensure we can query the specific scan information from its asset."""
    with models.Database() as session:
        asset = models.AndroidStore.create(
            package_name="a.b.c", application_name="fake_app"
        )
        session.add(asset)
        session.commit()
        scan = models.Scan(
            title="iOS Scan",
            progress=models.ScanProgress.NOT_STARTED,
            asset_instance=asset,
            asset_id=asset.id,
        )
        session.add(asset)
        session.commit()

    query = """
        query Scans($scanIds: [Int!]) {
            scans(scanIds: $scanIds) {
                scans {
                    id
                    assetInstance {
                        ... on AndroidStoreAssetType {
                            id
                            packageName
                            applicationName
                            scans {
                                id
                                title                                
                            }
                        }
                    }
                }
            }
        }
    """

    response = authenticated_flask_client.post(
        "/graphql",
        json={"query": query, "variables": {"scanIds": [scan.id]}},
    )

    assert response.status_code == 200, response.get_json()
    asset_data = response.get_json()["data"]["scans"]["scans"][0]["assetInstance"]
    assert asset_data["scans"][0]["id"] == str(scan.id)
    assert asset_data["scans"][0]["title"] == "iOS Scan"


@pytest.mark.skip
def testStopScanMutation_whenScanIsRunning_shouldStopScan(
    authenticated_flask_client: testing.FlaskClient,
    in_progress_web_scan: models.Scan,
    mocker: plugin.MockerFixture,
) -> None:
    """Test stopScan mutation when scan is running should stop scan."""
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_docker_installed",
        return_value=True,
    )
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_docker_working", return_value=True
    )
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_swarm_initialized",
        return_value=True,
    )
    mocker.patch("docker.from_env")

    mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.can_run", return_value=True
    )
    mocker.patch(
        "docker.DockerClient.services", return_value=services_model.ServiceCollection()
    )
    mocker.patch("docker.DockerClient.services.list", return_value=[])
    mocker.patch("docker.models.networks.NetworkCollection.list", return_value=[])
    mocker.patch("docker.models.configs.ConfigCollection.list", return_value=[])

    with models.Database() as session:
        nbr_scans_before = session.query(models.Scan).count()
        scan = session.query(models.Scan).get(in_progress_web_scan.id)
        scan_progress = scan.progress
        query = """
            mutation stopScan($scanId: Int!){
                stopScan(scanId: $scanId){
                    scan{
                        id
                    }
                }
            }
        """
        response = authenticated_flask_client.post(
            "/graphql", json={"query": query, "variables": {"scanId": str(scan.id)}}
        )

        assert response.status_code == 200, response.get_json()
        session.refresh(scan)
        scan = session.query(models.Scan).get(in_progress_web_scan.id)
        response_json = response.get_json()
        nbr_scans_after = session.query(models.Scan).count()
        assert response_json["data"] == {
            "stopScan": {"scan": {"id": str(in_progress_web_scan.id)}}
        }
        assert scan.progress.name == "STOPPED"
        assert scan.progress != scan_progress
        assert nbr_scans_after == nbr_scans_before


def testStopScanMutation_whenNoScanFound_shouldReturnError(
    authenticated_flask_client: testing.FlaskClient,
) -> None:
    """Test stopScan mutation when scan doesn't exist should return error message."""
    query = """
        mutation stopScan($scanId: Int!){
            stopScan(scanId: $scanId){
                scan{
                    id
                }
            }
        }
    """
    response = authenticated_flask_client.post(
        "/graphql", json={"query": query, "variables": {"scanId": "5"}}
    )

    assert response.status_code == 200, response.get_json()
    response_json = response.get_json()
    assert response_json["errors"][0]["message"] == "Scan not found."


def testQueryVulnerabilitiesOfKb_withPagination_shouldReturnPageInfo(
    authenticated_flask_client: testing.FlaskClient, android_scan: models.Scan
) -> None:
    """Test the kb vulnerabilities query with pagination, should return the correct pageInfo."""

    with models.Database() as session:
        kb_vulnerabilities = (
            session.query(models.Vulnerability)
            .filter(models.Vulnerability.id.in_([1, 2]))
            .all()
        )
        assert kb_vulnerabilities is not None

    query = """query Scans($scanIds: [Int!], $scanPage: Int, $scanElements: Int, $vulnPage: Int, $vulnElements: Int) {
        scans(scanIds: $scanIds, page: $scanPage, numberElements: $scanElements) {
            pageInfo {
                count
                numPages
                hasNext
                hasPrevious
            }
            scans {
                id
                title
                kbVulnerabilities {
                    highestRiskRating
                    vulnerabilities (page: $vulnPage, numberElements: $vulnElements){
                         pageInfo {Pages
                            hasNext
                      
                            count
                            numPages
                            hasNext
                            hasPrevious
                        }
                        vulnerabilities {
                            id
                        }
                    }
                }
            }
        }
    }
    """

    response = authenticated_flask_client.post(
        "/graphql",
        json={
            "query": query,
            "variables": {
                "scanPage": 1,
                "scanElements": 1,
                "vulnPage": 2,
                "vulnElements": 1,
            },
        },
    )

    assert response.status_code == 200, response.get_json()
    assert response.get_json()["data"]["scans"]["scans"][0]["kbVulnerabilities"][0][
        "vulnerabilities"
    ]["pageInfo"] == {
        "count": 3,
        "hasNext": True,
        "hasPrevious": True,
        "numPages": 3,
    }


def testPublishAgentGroupMutation_always_shouldPublishAgentGroup(
    authenticated_flask_client: testing.FlaskClient,
) -> None:
    """Ensure the publish agent group mutation creates an agent group."""

    query = """mutation publishAgentGroup($agentGroup: AgentGroupCreateInputType!) {
                      publishAgentGroup(agentGroup: $agentGroup) {
                        agentGroup {
                            key,
                            name,
                            agents {
                                agents {
                                    key,
                                    args {
                                        args {
                                            name
                                            type
                                            value
                                        }
                                    }
                                }
                            }
                        }
                      }
                    }"""

    variables = {
        "agentGroup": {
            "name": "test_agent_group",
            "description": "agent description",
            "agents": [
                {
                    "key": "agent_key",
                    "args": [{"name": "arg1", "type": "type1", "value": b"value1"}],
                }
            ],
        }
    }
    ubjson_data = ubjson.dumpb({"query": query, "variables": variables})

    response = authenticated_flask_client.post(
        "/graphql", data=ubjson_data, headers={"Content-Type": "application/ubjson"}
    )

    assert response.status_code == 200, ubjson.loadb(response.data)
    ag = ubjson.loadb(response.data)["data"]["publishAgentGroup"]["agentGroup"]
    agent_group_key = ag["key"]
    agent_group_name = ag["name"]
    agent_key = ag["agents"]["agents"][0]["key"]
    arg_name = ag["agents"]["agents"][0]["args"]["args"][0]["name"]
    arg_type = ag["agents"]["agents"][0]["args"]["args"][0]["type"]
    arg_value = ag["agents"]["agents"][0]["args"]["args"][0]["value"]
    assert agent_group_key == "agentgroup//test_agent_group"
    assert agent_group_name == "test_agent_group"
    assert agent_key == "agent_key"
    assert arg_name == "arg1"
    assert arg_type == "type1"
    assert isinstance(arg_value, bytes) is True
    assert arg_value == b"value1"


def testDeleteAgentGroupMutation_whenAgentGroupExist_deleteAgentGroup(
    authenticated_flask_client: testing.FlaskClient, agent_group: models.AgentGroup
) -> None:
    """Ensure the delete agent group mutation deletes the agent group."""
    with models.Database() as session:
        nbr_agent_groups_before_delete = session.query(models.AgentGroup).count()

    query = """
        mutation DeleteAgentGroup ($agentGroupId: Int!){
            deleteAgentGroup (agentGroupId: $agentGroupId) {
                result
            }
        }
    """

    response = authenticated_flask_client.post(
        "/graphql", json={"query": query, "variables": {"agentGroupId": agent_group.id}}
    )

    assert response.status_code == 200, response.get_json()
    assert response.get_json()["data"]["deleteAgentGroup"]["result"] is True
    with models.Database() as session:
        assert (
            session.query(models.AgentGroup).count()
            == nbr_agent_groups_before_delete - 1
        )


def testDeleteAgentGroupMutation_whenAgentGroupDoesNotExist_returnErrorMessage(
    authenticated_flask_client: testing.FlaskClient,
) -> None:
    """Ensure the delete agent group mutation returns an error message when the agent group does not exist."""
    query = """
        mutation DeleteAgentGroup ($agentGroupId: Int!){
            deleteAgentGroup (agentGroupId: $agentGroupId) {
                result
            }
        }
    """

    response = authenticated_flask_client.post(
        "/graphql", json={"query": query, "variables": {"agentGroupId": 42}}
    )

    assert response.status_code == 200, response.get_json()
    assert response.get_json()["errors"][0]["message"] == "AgentGroup not found."
