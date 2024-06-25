"""Unit tests for the oxo module."""

import io
import json
import os
import pathlib
import sys
from typing import Dict, Any

from docker.models import services as services_model
import httpx
import ubjson
from flask import testing
from pytest_mock import plugin
import pytest

from ostorlab.runtimes.local.models import models
from ostorlab.serve_app import import_utils
from ostorlab.serve_app.schema import schema as oxo_schema

RE_OXO_ENDPOINT = "https://api.ostorlab.co/apis/oxo"


INTROSPECT_ENUMS_QUERY = """
    {
        __schema {
            types {
                name
                kind
                enumValues {
                    name
                }
            }
        }
    }    
"""


INTROSPECT_INPUTS_QUERY = """
    {
        __schema {
            types {
                name
                kind
                inputFields {
                    name
                    type {
                        name
                        kind
                        ofType {
                            kind
                            name
                        }
                    }
                }
            }
        }
    }
"""

INTROSPECT_MUTATIONS_QUERY = """
{
    __schema {
        types {
            name
            kind
            fields {
                name
                type {
                    name
                    kind
                    ofType {
                        name
                        kind
                    }
                }
                args {
                    name
                    type {
                        kind
                        name
                        ofType {
                            kind
                            name
                            ofType {
                                name
                                kind
                            }
                        }
                    }
                }
            }
        }
    }
}
"""

INTROSPECT_QUERIES_QUERY = """
{
    __schema {
        types {
            name
            kind
            fields {
                name
                type {
                    name
                    kind
                    ofType {
                        name
                        kind
                    }
                }
                args {
                    name
                    type {
                        kind
                        name
                        ofType {
                            kind
                            name
                            ofType {
                                name
                                kind
                            }
                        }
                    }
                }
            }
        }
    }
}
"""


INTROSPECT_UNIONS_QUERY = """
{
    __schema {
        types {
            name
            kind
            possibleTypes {
                kind
                name
                ofType {
                    kind
                    name
                }
            }
        }
    }
}    
"""


INTROSPECT_TYPES_QUERY = """
    {
        __schema {
            types {
                name
                kind
                fields {
                    name
                    type {
                        kind
                        name
                        fields {
                            name
                        }
                        ofType {
                            name
                            kind
                        }
                    }
                }
            }
        }
    }
"""


def testImportScanMutation_always_shouldImportScan(
    authenticated_flask_client: testing.FlaskClient,
    zip_file_bytes: bytes,
    mocker: plugin.MockerFixture,
    db_engine_path: str,
) -> None:
    """Test importScan mutation."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)

    with models.Database() as session:
        nbr_scans_before_import = session.query(models.Scan).count()
        nbr_assets_before_import = session.query(models.Asset).count()
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
        assert session.query(models.Asset).count() == nbr_assets_before_import + 1
        asset = session.query(models.Asset).first()
        assert asset.type == "ios_file"
        assert asset.bundle_id == "ostorlab.swiftvulnerableapp"


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
                    progress
                    createdTime
                    assets {
                            ... on OxoIOSFileAssetType {
                                path
                            }
                            
                            ... on OxoIOSStoreAssetType {
                                bundleId
                            }
                        }
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
    assert scan1["assets"][0]["path"] == "/path/to/file"
    assert scan1["progress"] == scans[0].progress.name
    assert scan1["createdTime"] == scans[0].created_time.isoformat()
    assert scan2["id"] == "2"
    assert scan2["title"] == scans[1].title
    assert scan2["assets"][0]["bundleId"] == "com.example.app"
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
                    assets {
                            ... on OxoIOSFileAssetType {
                                path
                            }
                            
                            ... on OxoIOSStoreAssetType {
                                bundleId
                            }
                        }
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
    assert scan1["assets"][0]["path"] == "/path/to/file"
    assert scan1["progress"] == scans[0].progress.name
    assert scan1["createdTime"] == scans[0].created_time.isoformat()
    assert scan2["id"] == "2"
    assert scan2["title"] == scans[1].title
    assert scan2["assets"][0]["bundleId"] == "com.example.app"
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
                    assets {
                            ... on OxoIOSFileAssetType {
                                path
                            }
                            
                            ... on OxoIOSStoreAssetType {
                                bundleId
                            }
                        }
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
    assert scan1["assets"][0]["path"] == "/path/to/file"
    assert scan1["progress"] == scans[0].progress.name
    assert scan1["createdTime"] == scans[0].created_time.isoformat()
    assert scan2["id"] == "2"
    assert scan2["title"] == scans[1].title
    assert scan2["assets"][0]["bundleId"] == "com.example.app"
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
                        assets {
                            ... on OxoIOSFileAssetType {
                                path
                            }
                            
                            ... on OxoIOSStoreAssetType {
                                bundleId
                            }
                        }
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
    asset = response.get_json()["data"]["scans"]["scans"][0]["assets"][0]
    assert asset["bundleId"] == "com.example.app"
    asset = response.get_json()["data"]["scans"]["scans"][1]["assets"][0]
    assert asset["path"] == "/path/to/file"


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
                        assets {
                            ... on OxoIOSFileAssetType {
                                path
                            }
                            
                            ... on OxoIOSStoreAssetType {
                                bundleId
                            }
                        }
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
    asset = response.get_json()["data"]["scans"]["scans"][0]["assets"][0]
    assert asset["bundleId"] == "com.example.app"
    asset = response.get_json()["data"]["scans"]["scans"][1]["assets"][0]
    assert asset["path"] == "/path/to/file"


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
                assets {
                ... on OxoAndroidFileAssetType {
                        id
                        packageName
                        path
                    }
                }
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

    assets = scan_data["assets"]
    assert len(assets) == 1
    assert assets[0]["packageName"] == "com.example.app"
    assert assets[0]["path"] == "/path/to/file"


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
    mocker: plugin.MockerFixture,
    db_engine_path: str,
) -> None:
    """Test the vulnerabilities query with pagination, should return the correct pageInfo."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
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
    authenticated_flask_client: testing.FlaskClient,
    agent_groups: models.AgentGroup,
    mocker: plugin.MockerFixture,
    db_engine_path: str,
) -> None:
    """Test query for multiple agent groups."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
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
                        assetTypes
                        yamlSource
                        agents {
                            agents {
                                key
                                args {
                                    args {
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
        "/graphql",
        data=ubjson_data,
        headers={"Content-Type": "application/ubjson", "Accept": "application/ubjson"},
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
    assert agent_group1["assetTypes"] == ["WEB"]
    assert agent_group2["name"] == agent_groups[1].name
    assert agent_group2["description"] == agent_groups[1].description
    assert agent_group2["key"] == f"agentgroup//{agent_groups[1].name}"
    assert agent_group2["createdTime"] == agent_groups[1].created_time.isoformat()
    assert agent_group2["assetTypes"] == ["ANDROID"]
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
    assert len(agent2_args) == 4
    assert agent1_args[0]["name"] == "arg1"
    assert agent1_args[0]["type"] == "number"
    assert (
        models.AgentArgument.from_bytes(agent1_args[0]["type"], agent1_args[0]["value"])
        == 42
    )
    assert agent2_args[0]["name"] == "arg2"
    assert agent2_args[0]["type"] == "string"
    assert (
        models.AgentArgument.from_bytes(agent2_args[0]["type"], agent2_args[0]["value"])
        == "hello"
    )
    assert agent2_args[1]["name"] == "arg3"
    assert agent2_args[1]["type"] == "array"
    assert models.AgentArgument.from_bytes(
        agent2_args[1]["type"], agent2_args[1]["value"]
    ) == ["hello", "world"]
    assert agent2_args[2]["name"] == "arg4"
    assert agent2_args[2]["type"] == "object"
    assert models.AgentArgument.from_bytes(
        agent2_args[2]["type"], agent2_args[2]["value"]
    ) == {"hello": "world"}
    assert agent2_args[3]["name"] == "arg5"
    assert agent2_args[3]["type"] == "boolean"
    assert (
        models.AgentArgument.from_bytes(agent2_args[3]["type"], agent2_args[3]["value"])
        is False
    )
    yaml_source_ag1 = agent_group1["yamlSource"]
    yaml_source_ag2 = agent_group2["yamlSource"]
    assert "kind: AgentGroup" in yaml_source_ag1
    assert "name: Agent Group 1" in yaml_source_ag1
    assert "kind: AgentGroup" in yaml_source_ag2
    assert "name: Agent Group 2" in yaml_source_ag2


def testQuerySingleAgentGroup_always_shouldReturnSingleAgentGroup(
    authenticated_flask_client: testing.FlaskClient,
    agent_groups: models.AgentGroup,
    mocker: plugin.MockerFixture,
    db_engine_path: str,
) -> None:
    """Test query for a single agent group."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
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
                                key
                                args {
                                    args {
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
        "/graphql",
        data=ubjson_data,
        headers={"Content-Type": "application/ubjson", "Accept": "application/ubjson"},
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
    assert len(agent2_args) == 4
    assert agent1_args[0]["name"] == "arg1"
    assert agent1_args[0]["type"] == "number"
    assert (
        models.AgentArgument.from_bytes(agent1_args[0]["type"], agent1_args[0]["value"])
        == 42
    )
    assert agent2_args[0]["name"] == "arg2"
    assert agent2_args[0]["type"] == "string"
    assert (
        models.AgentArgument.from_bytes(agent2_args[0]["type"], agent2_args[0]["value"])
        == "hello"
    )
    assert agent2_args[1]["name"] == "arg3"
    assert agent2_args[1]["type"] == "array"
    assert models.AgentArgument.from_bytes(
        agent2_args[1]["type"], agent2_args[1]["value"]
    ) == ["hello", "world"]
    assert agent2_args[2]["name"] == "arg4"
    assert agent2_args[2]["type"] == "object"
    assert models.AgentArgument.from_bytes(
        agent2_args[2]["type"], agent2_args[2]["value"]
    ) == {"hello": "world"}
    assert agent2_args[3]["name"] == "arg5"
    assert agent2_args[3]["type"] == "boolean"
    assert (
        models.AgentArgument.from_bytes(agent2_args[3]["type"], agent2_args[3]["value"])
        is False
    )


def testQueryAgentGroupWithAssetType_always_shouldReturnCorrectResults(
    authenticated_flask_client: testing.FlaskClient,
    agent_groups: models.AgentGroup,
    mocker: plugin.MockerFixture,
    db_engine_path: str,
) -> None:
    """Test query for agent group with asset type."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    with models.Database() as session:
        agent_group = session.query(models.AgentGroup).filter_by(id=1).first()
        assert agent_group is not None

    query = """
            query AgentGroup ($agentGroupIds: [Int!], $assetType: String!){
                agentGroups (agentGroupIds: $agentGroupIds, assetType: $assetType) {
                    agentGroups {
                        id
                        name
                        description
                        createdTime
                        key
                        assetTypes
                        agents {
                            agents {
                                key
                                args {
                                    args {
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
    variables = {"agentGroupIds": [1], "assetType": "WEB"}
    ubjson_data = ubjson.dumpb({"query": query, "variables": variables})

    response = authenticated_flask_client.post(
        "/graphql",
        data=ubjson_data,
        headers={"Content-Type": "application/ubjson", "Accept": "application/ubjson"},
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
    assert agent_group_data["assetTypes"] == ["WEB"]
    agent_group_agents = agent_group_data["agents"]["agents"]
    assert len(agent_group_agents) == 2
    assert agent_group_agents[0]["key"] == "agent/ostorlab/agent1"
    assert agent_group_agents[1]["key"] == "agent/ostorlab/agent2"
    agent_args = agent_group_agents[0]["args"]["args"]
    assert len(agent_args) == 1
    assert agent_args[0]["name"] == "arg1"
    assert agent_args[0]["type"] == "number"
    assert (
        models.AgentArgument.from_bytes(agent_args[0]["type"], agent_args[0]["value"])
        == 42
    )


def testQueryAgentGroupsWithPagination_always_returnPageInfo(
    authenticated_flask_client: testing.FlaskClient,
    agent_groups: models.AgentGroup,
    mocker: plugin.MockerFixture,
    db_engine_path: str,
) -> None:
    """Test query for agent groups with pagination."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
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
                                key
                                args {
                                    args {
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
        headers={"Content-Type": "application/ubjson", "Accept": "application/ubjson"},
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
    """Ensure the android store asset is created successfully through the createAssets API."""
    del clean_db
    query = """
        mutation createAndroidStore($assets: [OxoAssetInputType]!) {
            createAssets(assets: $assets) {
                assets {
                    ... on OxoAndroidStoreAssetType {
                            id
                            applicationName
                            packageName
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
                        "androidStore": [
                            {
                                "applicationName": "fake_app1",
                                "packageName": "a.b.c",
                            },
                            {
                                "applicationName": "fake_app2",
                                "packageName": "d.e.f",
                            },
                        ]
                    }
                ]
            },
        },
    )

    assert resp.status_code == 200, resp.get_json()
    asset1 = resp.get_json()["data"]["createAssets"]["assets"][0]
    asset2 = resp.get_json()["data"]["createAssets"]["assets"][1]
    assert asset1["id"] is not None
    assert asset1["packageName"] == "a.b.c"
    assert asset1["applicationName"] == "fake_app1"
    assert asset2["id"] is not None
    assert asset2["packageName"] == "d.e.f"
    assert asset2["applicationName"] == "fake_app2"
    with models.Database() as session:
        assert session.query(models.AndroidStore).count() == 2
        assert session.query(models.AndroidStore).all()[0].package_name == "a.b.c"
        assert (
            session.query(models.AndroidStore).all()[0].application_name == "fake_app1"
        )
        assert session.query(models.AndroidStore).all()[1].package_name == "d.e.f"
        assert (
            session.query(models.AndroidStore).all()[1].application_name == "fake_app2"
        )


def testCreateAsset_iOSStore_createsNewAsset(
    authenticated_flask_client: testing.FlaskClient, clean_db: None
) -> None:
    """Ensure the ios store asset is created successfully through the createAssets API."""
    del clean_db
    query = """
        mutation createiOSStore($assets: [OxoAssetInputType]!) {
            createAssets(assets: $assets) {
                assets {
                    ... on OxoIOSStoreAssetType {
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
                        "iosStore": [
                            {
                                "applicationName": "fake_app1",
                                "bundleId": "a.b.c",
                            },
                            {
                                "applicationName": "fake_app2",
                                "bundleId": "d.e.f",
                            },
                        ]
                    }
                ]
            },
        },
    )

    assert resp.status_code == 200, resp.get_json()
    asset1 = resp.get_json()["data"]["createAssets"]["assets"][0]
    asset2 = resp.get_json()["data"]["createAssets"]["assets"][1]
    assert asset1["id"] is not None
    assert asset1["bundleId"] == "a.b.c"
    assert asset1["applicationName"] == "fake_app1"
    assert asset2["id"] is not None
    assert asset2["bundleId"] == "d.e.f"
    assert asset2["applicationName"] == "fake_app2"
    with models.Database() as session:
        assert session.query(models.IosStore).count() == 2
        assert session.query(models.IosStore).all()[0].bundle_id == "a.b.c"
        assert session.query(models.IosStore).all()[0].application_name == "fake_app1"
        assert session.query(models.IosStore).all()[1].bundle_id == "d.e.f"
        assert session.query(models.IosStore).all()[1].application_name == "fake_app2"


def testCreateAsset_url_createsNewAsset(
    authenticated_flask_client: testing.FlaskClient, clean_db: None
) -> None:
    """Ensure the url asset & its links are created successfully through the createAssets API."""
    del clean_db
    query = """
        mutation createUrl($assets: [OxoAssetInputType]!) {
            createAssets(assets: $assets) {
                assets {
                    ... on OxoUrlsAssetType {
                        id
                        links {
                            url
                            method
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
                        "link": [
                            {"url": "https://www.google.com", "method": "GET"},
                            {"url": "https://www.tesla.com"},
                        ]
                    }
                ]
            },
        },
    )

    assert resp.status_code == 200, resp.get_json()
    asset_data = resp.get_json()["data"]["createAssets"]["assets"][0]
    assert asset_data["id"] is not None
    assert asset_data["links"] == [
        {"method": "GET", "url": "https://www.google.com"},
        {"method": "GET", "url": "https://www.tesla.com"},
    ]
    with models.Database() as session:
        assert session.query(models.Urls).count() == 1
        urls_asset_id = session.query(models.Urls).first().id
        links = session.query(models.Link).filter_by(urls_asset_id=urls_asset_id).all()
        assert len(links) == 2
        assert links[0].url == "https://www.google.com"
        assert links[0].method == "GET"
        assert links[1].url == "https://www.tesla.com"
        assert links[1].method == "GET"


def testCreateAsset_network_createsNewAsset(
    authenticated_flask_client: testing.FlaskClient, clean_db: None
) -> None:
    """Ensure the network asset & its ips are created successfully through the createAssets API."""
    del clean_db
    query = """
        mutation createNetwork($assets: [OxoAssetInputType]!) {
            createAssets(assets: $assets) {
                assets {
                    ... on OxoNetworkAssetType {
                        id
                        networks {
                            host
                            mask
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
                    {"ip": [{"host": "8.8.8.8", "mask": "24"}, {"host": "42.42.42.42"}]}
                ]
            },
        },
    )

    assert resp.status_code == 200, resp.get_json()
    asset_data = resp.get_json()["data"]["createAssets"]["assets"][0]
    assert asset_data["id"] is not None
    assert asset_data["networks"] == [
        {"host": "8.8.8.8", "mask": "24"},
        {"host": "42.42.42.42", "mask": "32"},
    ]
    with models.Database() as session:
        assert session.query(models.Network).count() == 1
        network_asset_id = session.query(models.Network).first().id
        networks = (
            session.query(models.IPRange)
            .filter_by(network_asset_id=network_asset_id)
            .all()
        )
        assert len(networks) == 2
        assert networks[0].host == "8.8.8.8"
        assert networks[0].mask == "24"
        assert networks[1].host == "42.42.42.42"
        assert networks[1].mask == "32"


def testCreateAsset_domain_createsNewAsset(
    authenticated_flask_client: testing.FlaskClient, clean_db: None
) -> None:
    """Ensure the domain asset is created successfully through the createAssets API."""
    del clean_db
    query = """
        mutation createDomain($assets: [OxoAssetInputType]!) {
            createAssets(assets: $assets) {
                assets {
                    ... on OxoDomainNameAssetsType {
                        id
                        domainNames {
                            name
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
                    {"domain": [{"name": "www.google.com"}, {"name": "www.tesla.com"}]}
                ]
            },
        },
    )

    assert resp.status_code == 200, resp.get_json()
    asset_data = resp.get_json()["data"]["createAssets"]["assets"][0]
    assert asset_data["id"] is not None
    assert asset_data["domainNames"] == [
        {"name": "www.google.com"},
        {"name": "www.tesla.com"},
    ]
    with models.Database() as session:
        assert session.query(models.DomainAsset).count() == 1
        domain_asset_id = session.query(models.DomainAsset).first().id
        domains = (
            session.query(models.DomainName)
            .filter_by(domain_asset_id=domain_asset_id)
            .all()
        )
        assert len(domains) == 2
        assert domains[0].name == "www.google.com"
        assert domains[1].name == "www.tesla.com"


def testCreateAsset_androidApkFile_createsNewAsset(
    authenticated_flask_client: testing.FlaskClient, clean_db: None
) -> None:
    """Ensure the android file is created successfully through the createAssets API."""
    del clean_db
    query = """
        mutation createAndroidFile($assets: [OxoAssetInputType]!) {
            createAssets(assets: $assets) {
                assets {
                    ... on OxoAndroidFileAssetType {
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
                            "androidApkFile": [
                                {
                                    "file": None,
                                    "packageName": "a.b.c",
                                }
                            ]
                        }
                    ]
                },
            }
        ),
        "0": apk_path.open("rb"),
        "map": json.dumps({"0": ["variables.assets.0.androidApkFile.0.file"]}),
    }

    resp = authenticated_flask_client.post(
        "/graphql",
        data=data,
    )

    assert resp.status_code == 200, resp.get_json()
    asset_data = resp.get_json()["data"]["createAssets"]["assets"][0]
    assert asset_data["id"] is not None
    assert asset_data["packageName"] == "a.b.c"
    if sys.platform == "win32":
        assert "\\.ostorlab\\uploads\\android_" in asset_data["path"]
    else:
        assert ".ostorlab/uploads/android_" in asset_data["path"]
    with models.Database() as session:
        assert session.query(models.AndroidFile).count() == 1
        assert session.query(models.AndroidFile).all()[0].package_name == "a.b.c"
        if sys.platform == "win32":
            assert (
                "\\.ostorlab\\uploads\\android_"
                in session.query(models.AndroidFile).all()[0].path
            )
        else:
            assert (
                ".ostorlab/uploads/android_"
                in session.query(models.AndroidFile).all()[0].path
            )


def testCreateAsset_androidAabFile_createsNewAsset(
    authenticated_flask_client: testing.FlaskClient, clean_db: None
) -> None:
    """Ensure the android file is created successfully through the createAssets API."""
    del clean_db
    query = """
        mutation createAndroidFile($assets: [OxoAssetInputType]!) {
            createAssets(assets: $assets) {
                assets {
                    ... on OxoAndroidFileAssetType {
                        id
                        packageName
                        path
                    }
                }
            }
        }
    """
    apk_path = pathlib.Path(__file__).parent.parent / "files" / "health.aab"
    data = {
        "operations": json.dumps(
            {
                "query": query,
                "variables": {
                    "assets": [
                        {
                            "androidAabFile": [
                                {
                                    "file": None,
                                    "packageName": "a.b.c",
                                }
                            ]
                        }
                    ]
                },
            }
        ),
        "0": apk_path.open("rb"),
        "map": json.dumps({"0": ["variables.assets.0.androidAabFile.0.file"]}),
    }

    resp = authenticated_flask_client.post(
        "/graphql",
        data=data,
    )

    assert resp.status_code == 200, resp.get_json()
    asset_data = resp.get_json()["data"]["createAssets"]["assets"][0]
    assert asset_data["id"] is not None
    assert asset_data["packageName"] == "a.b.c"
    if sys.platform == "win32":
        assert "\\.ostorlab\\uploads\\android_" in asset_data["path"]
    else:
        assert ".ostorlab/uploads/android_" in asset_data["path"]
    with models.Database() as session:
        assert session.query(models.AndroidFile).count() == 1
        assert session.query(models.AndroidFile).all()[0].package_name == "a.b.c"
        if sys.platform == "win32":
            assert (
                "\\.ostorlab\\uploads\\android_"
                in session.query(models.AndroidFile).all()[0].path
            )
        else:
            assert (
                ".ostorlab/uploads/android_"
                in session.query(models.AndroidFile).all()[0].path
            )


def testCreateAsset_iOSFile_createsNewAsset(
    authenticated_flask_client: testing.FlaskClient, clean_db: None
) -> None:
    """Ensure the iOS file is created successfully through the createAssets API."""
    del clean_db
    query = """
        mutation createAndroidFile($assets: [OxoAssetInputType]!) {
            createAssets(assets: $assets) {
                assets {
                    ... on OxoIOSFileAssetType {
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
                            "iosFile": [
                                {
                                    "file": None,
                                    "bundleId": "a.b.c",
                                }
                            ]
                        }
                    ]
                },
            }
        ),
        "0": apk_path.open("rb"),
        "map": json.dumps({"0": ["variables.assets.0.iosFile.0.file"]}),
    }

    resp = authenticated_flask_client.post(
        "/graphql",
        data=data,
    )

    assert resp.status_code == 200, resp.get_json()
    asset_data = resp.get_json()["data"]["createAssets"]["assets"][0]
    assert asset_data["id"] is not None
    assert asset_data["bundleId"] == "a.b.c"
    if sys.platform == "win32":
        assert "\\.ostorlab\\uploads\\ios_" in asset_data["path"]
    else:
        assert ".ostorlab/uploads/ios_" in asset_data["path"]
    with models.Database() as session:
        assert session.query(models.IosFile).count() == 1
        assert session.query(models.IosFile).all()[0].bundle_id == "a.b.c"
        if sys.platform == "win32":
            assert (
                "\\.ostorlab\\uploads\\ios_"
                in session.query(models.IosFile).all()[0].path
            )
        else:
            assert (
                ".ostorlab/uploads/ios_" in session.query(models.IosFile).all()[0].path
            )


def testCreateAsset_whenMultipleAssets_shouldCreateAll(
    authenticated_flask_client: testing.FlaskClient, clean_db: None
) -> None:
    """Ensure the create asset mutation creates all the provided assets assuming, they are independently valid."""
    del clean_db
    query = """
        mutation createAssets($assets: [OxoAssetInputType]!) {
            createAssets(assets: $assets) {
                assets {
                    ... on OxoAndroidStoreAssetType {
                        id
                        packageName
                        applicationName
                    }
                    ... on OxoIOSStoreAssetType {
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
                        "androidStore": [
                            {
                                "applicationName": "fake_app",
                                "packageName": "a.b.c",
                            }
                        ]
                    },
                    {
                        "iosStore": [
                            {
                                "applicationName": "fake_app",
                                "bundleId": "a.b.c",
                            }
                        ]
                    },
                ]
            },
        },
    )

    assert resp.status_code == 200, resp.get_json()
    assets_data = resp.get_json()["data"]["createAssets"]["assets"]
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
        mutation createAssets($assets: [OxoAssetInputType]!) {
            createAssets(assets: $assets) {
                assets {
                    ... on OxoAndroidStoreAssetType {
                        id
                        packageName
                        applicationName
                    }
                    ... on OxoIOSStoreAssetType {
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
                        "androidStore": [
                            {
                                "applicationName": "fake_app",
                                "packageName": "a.b.c",
                            }
                        ],
                        "iosStore": [
                            {
                                "applicationName": "fake_app",
                                "bundleId": "a.b.c",
                            }
                        ],
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
        mutation createAssets($assets: [OxoAssetInputType]!) {
            createAssets(assets: $assets) {
                assets {
                    ... on OxoAndroidStoreAssetType {
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
    mocker: plugin.MockerFixture,
    db_engine_path: str,
) -> None:
    """Ensure we can query the specific asset information (depending on the target type) from the scan."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    with models.Database() as session:
        scan = models.Scan(
            title="iOS Scan",
            progress=models.ScanProgress.NOT_STARTED,
        )
        session.add(scan)
        session.commit()
        asset = models.AndroidStore(
            package_name="a.b.c", application_name="fake_app", scan_id=scan.id
        )
        session.add(asset)
        session.commit()

    query = """
        query Scans($scanIds: [Int!]) {
            scans(scanIds: $scanIds) {
                scans {
                    id
                    title
                    progress
                    createdTime
                    assets {
                        ... on OxoAndroidStoreAssetType {
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
    assert scan_data["assets"][0]["packageName"] == asset.package_name
    assert scan_data["assets"][0]["applicationName"] == asset.application_name


def testQueryAssets_whenScanHasMultipleAssets_shouldReturnAllAssets(
    authenticated_flask_client: testing.FlaskClient, multiple_assets_scan: models.Scan
) -> None:
    """Ensure we can query the specific scan information from its asset."""
    query = """
        query Scans($scanIds: [Int!]) {
            scans(scanIds: $scanIds) {
                scans {
                    id
                    assets {
                        ... on OxoNetworkAssetType {
                            networks {
                                host
                                mask
                            }
                        }
                        
                        ... on OxoAndroidFileAssetType {
                            id
                            path
                        }
                    }
                }
            }
        }
    """

    response = authenticated_flask_client.post(
        "/graphql",
        json={"query": query, "variables": {"scanIds": [multiple_assets_scan.id]}},
    )

    assert response.status_code == 200, response.get_json()
    asset1 = response.get_json()["data"]["scans"]["scans"][0]["assets"][0]
    asset2 = response.get_json()["data"]["scans"]["scans"][0]["assets"][1]
    assert "test.apk" in asset1["path"]
    assert asset2["networks"] == [
        {"host": "8.8.8.8", "mask": "32"},
        {"host": "8.8.4.4", "mask": "32"},
    ]


def testStopScanMutation_whenScanIsRunning_shouldStopScan(
    authenticated_flask_client: testing.FlaskClient,
    in_progress_web_scan: models.Scan,
    mocker: plugin.MockerFixture,
    db_engine_path: str,
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
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
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
    mocker: plugin.MockerFixture,
    db_engine_path: str,
    clean_db: None,
) -> None:
    """Test stopScan mutation when scan doesn't exist should return error message."""
    del clean_db
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
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
    authenticated_flask_client: testing.FlaskClient,
    android_scan: models.Scan,
    mocker: plugin.MockerFixture,
    db_engine_path: str,
) -> None:
    """Test the kb vulnerabilities query with pagination, should return the correct pageInfo."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
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
    mocker: plugin.MockerFixture,
    db_engine_path: str,
) -> None:
    """Ensure the publish agent group mutation creates an agent group."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    query = """mutation publishAgentGroup($agentGroup: OxoAgentGroupCreateInputType!) {
                      publishAgentGroup(agentGroup: $agentGroup) {
                        agentGroup {
                            key,
                            name,
                            assetTypes,
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
            "assetTypes": ["WEB", "NETWORK"],
        }
    }
    ubjson_data = ubjson.dumpb({"query": query, "variables": variables})

    response = authenticated_flask_client.post(
        "/graphql",
        data=ubjson_data,
        headers={"Content-Type": "application/ubjson", "Accept": "application/ubjson"},
    )

    assert response.status_code == 200, ubjson.loadb(response.data)
    ag = ubjson.loadb(response.data)["data"]["publishAgentGroup"]["agentGroup"]
    agent_group_key = ag["key"]
    agent_group_name = ag["name"]
    agent_key = ag["agents"]["agents"][0]["key"]
    arg_name = ag["agents"]["agents"][0]["args"]["args"][0]["name"]
    arg_type = ag["agents"]["agents"][0]["args"]["args"][0]["type"]
    arg_value = ag["agents"]["agents"][0]["args"]["args"][0]["value"]
    asset_types = ag["assetTypes"]
    assert agent_group_key == "agentgroup//test_agent_group"
    assert agent_group_name == "test_agent_group"
    assert agent_key == "agent_key"
    assert arg_name == "arg1"
    assert arg_type == "type1"
    assert isinstance(arg_value, bytes) is True
    assert arg_value == b"value1"
    assert asset_types == ["WEB", "NETWORK"]


def testDeleteAgentGroupMutation_whenAgentGroupExist_deleteAgentGroup(
    authenticated_flask_client: testing.FlaskClient,
    agent_group: models.AgentGroup,
    mocker: plugin.MockerFixture,
    db_engine_path: str,
) -> None:
    """Ensure the delete agent group mutation deletes the agent group."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
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
    mocker: plugin.MockerFixture,
    db_engine_path: str,
    clean_db: None,
) -> None:
    """Ensure the delete agent group mutation returns an error message when the agent group does not exist."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
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


def testRunScanMutation_whenNetworkAsset_shouldRunScan(
    authenticated_flask_client: testing.FlaskClient,
    agent_group_nmap: models.AgentGroup,
    network_asset: models.Asset,
    scan: models.Scan,
    mocker: plugin.MockerFixture,
) -> None:
    """Test RunScanMutation for Network asset."""
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
    scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan", return_value=scan
    )
    query = """
        mutation RunScan($scan: OxoAgentScanInputType!) {
            runScan(
                scan: $scan
            ) {
        scan {
            id
            title
            progress
            assets {
                ... on OxoNetworkAssetType {
                    id
                    networks {
                        host
                        mask
                    }
                }
            }
        }
            }
        }
    """
    variables = {
        "scan": {
            "title": "Test Scan Network Asset",
            "assetIds": [network_asset.id],
            "agentGroupId": agent_group_nmap.id,
        },
    }

    response = authenticated_flask_client.post(
        "/graphql", json={"query": query, "variables": variables}
    )

    assert response.status_code == 200, response.get_json()
    res_scan = response.get_json()["data"]["runScan"]["scan"]
    assert int(res_scan["id"]) == scan.id
    assert res_scan["title"] == scan.title
    assert res_scan["progress"] == scan.progress.name
    assert len(res_scan["assets"]) == 1
    assert int(res_scan["assets"][0]["id"]) == network_asset.id
    assert res_scan["assets"][0]["networks"] == [
        {"host": "8.8.8.8", "mask": "32"},
        {"host": "8.8.4.4", "mask": "24"},
    ]
    args = scan_mock.call_args[1]
    assert args["title"] == "Test Scan Network Asset"
    assert args["agent_group_definition"].agents[0].key == "agent/ostorlab/nmap"
    assert len(args["assets"]) == 2
    assert args["assets"][0].host == "8.8.8.8"
    assert args["assets"][0].mask == "32"
    assert args["assets"][1].host == "8.8.4.4"
    assert args["assets"][1].mask == "24"


def testRunScanMutation_whenDomainAsset_shouldRunScan(
    authenticated_flask_client: testing.FlaskClient,
    agent_group_nmap: models.AgentGroup,
    domain_asset: models.DomainAsset,
    scan: models.Scan,
    mocker: plugin.MockerFixture,
    run_scan_mock2: None,
) -> None:
    """Test RunScanMutation for Domain asset."""
    scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan", return_value=scan
    )
    query = """
        mutation RunScan($scan: OxoAgentScanInputType!) {
            runScan(
                scan: $scan
            ) {
                scan {
                    id
                    title
                    progress
                    assets {
                        ... on OxoDomainNameAssetsType {
                            id
                            domainNames {
                                name
                            }
                        }
                    }
                }
            }
        }
    """
    variables = {
        "scan": {
            "title": "Test Scan Domain Asset",
            "assetIds": [domain_asset.id],
            "agentGroupId": agent_group_nmap.id,
        },
    }

    response = authenticated_flask_client.post(
        "/graphql", json={"query": query, "variables": variables}
    )

    assert response.status_code == 200, response.get_json()
    res_scan = response.get_json()["data"]["runScan"]["scan"]
    assert int(res_scan["id"]) == scan.id
    assert res_scan["title"] == scan.title
    assert res_scan["progress"] == scan.progress.name
    assert len(res_scan["assets"]) == 1
    assert int(res_scan["assets"][0]["id"]) == domain_asset.id
    assert res_scan["assets"][0]["domainNames"] == [
        {"name": "google.com"},
        {"name": "tesla.com"},
    ]
    args = scan_mock.call_args[1]
    assert args["title"] == "Test Scan Domain Asset"
    assert args["agent_group_definition"].agents[0].key == "agent/ostorlab/nmap"
    assert len(args["assets"]) == 2
    assert args["assets"][0].name == "google.com"
    assert args["assets"][1].name == "tesla.com"


def testRunScanMutation_whenUrl_shouldRunScan(
    authenticated_flask_client: testing.FlaskClient,
    agent_group_nmap: models.AgentGroup,
    url_asset: models.Urls,
    scan: models.Scan,
    mocker: plugin.MockerFixture,
) -> None:
    """Test RunScanMutation for Url asset."""
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
    scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan", return_value=scan
    )
    query = """
        mutation RunScan($scan: OxoAgentScanInputType!) {
            runScan(
                scan: $scan
            ) {
                scan {
                    id
                    title
                    progress
                    assets {
                        ... on OxoUrlsAssetType {
                            id
                            links {
                                url
                                method
                            }
                        }
                    }                    
                }
            }
        }
    """
    variables = {
        "scan": {
            "title": "Test Scan Url Asset",
            "assetIds": [url_asset.id],
            "agentGroupId": agent_group_nmap.id,
        },
    }

    response = authenticated_flask_client.post(
        "/graphql", json={"query": query, "variables": variables}
    )

    assert response.status_code == 200, response.get_json()
    res_scan = response.get_json()["data"]["runScan"]["scan"]
    assert int(res_scan["id"]) == scan.id
    assert res_scan["title"] == scan.title
    assert res_scan["progress"] == scan.progress.name
    assert len(res_scan["assets"]) == 1
    assert int(res_scan["assets"][0]["id"]) == url_asset.id
    assert res_scan["assets"][0]["links"] == [
        {"method": "GET", "url": "https://google.com"},
        {"method": "GET", "url": "https://tesla.com"},
    ]
    args = scan_mock.call_args[1]
    assert args["title"] == "Test Scan Url Asset"
    assert args["agent_group_definition"].agents[0].key == "agent/ostorlab/nmap"
    assert len(args["assets"]) == 2
    assert args["assets"][0].url == "https://google.com"
    assert args["assets"][0].method == "GET"
    assert args["assets"][1].url == "https://tesla.com"
    assert args["assets"][1].method == "GET"


def testRunScanMutation_whenAndroidFile_shouldRunScan(
    authenticated_flask_client: testing.FlaskClient,
    agent_group_trufflehog: models.AgentGroup,
    android_file_asset: models.AndroidFile,
    scan: models.Scan,
    mocker: plugin.MockerFixture,
) -> None:
    """Test RunScanMutation for AndroidFile asset."""
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
    scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan", return_value=scan
    )
    query = """
        mutation RunScan($scan: OxoAgentScanInputType!) {
            runScan(
                scan: $scan
            ) {
                scan {
                    id
                    title
                    progress
                    assets {
                        ... on OxoAndroidFileAssetType {
                            id
                            path
                            packageName
                        }
                    }
                }
            }
        }
    """
    variables = {
        "scan": {
            "title": "Test Scan Android File",
            "assetIds": [android_file_asset.id],
            "agentGroupId": agent_group_trufflehog.id,
        },
    }

    response = authenticated_flask_client.post(
        "/graphql", json={"query": query, "variables": variables}
    )

    assert response.status_code == 200, response.get_json()
    res_scan = response.get_json()["data"]["runScan"]["scan"]
    assert int(res_scan["id"]) == scan.id
    assert res_scan["title"] == scan.title
    assert res_scan["progress"] == scan.progress.name
    assert len(res_scan["assets"]) == 1
    assert int(res_scan["assets"][0]["id"]) == android_file_asset.id
    assert "test.apk" in res_scan["assets"][0]["path"]
    args = scan_mock.call_args[1]
    assert args["title"] == "Test Scan Android File"
    assert args["agent_group_definition"].agents[0].key == "agent/ostorlab/trufflehog"
    assert len(args["assets"]) == 1
    assert "test.apk" in args["assets"][0].path


def testRunScanMutation_whenIosFile_shouldRunScan(
    authenticated_flask_client: testing.FlaskClient,
    agent_group_trufflehog: models.AgentGroup,
    ios_file_asset: models.IosFile,
    scan: models.Scan,
    mocker: plugin.MockerFixture,
) -> None:
    """Test RunScanMutation for IosFile asset."""
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
    scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan", return_value=scan
    )
    query = """
        mutation RunScan($scan: OxoAgentScanInputType!) {
            runScan(
                scan: $scan
            ) {
                scan {
                    id
                    title
                    progress
                    assets {
                        ... on OxoIOSFileAssetType {
                            id
                            path
                            bundleId
                        }
                    }
                }
            }
        }
    """
    variables = {
        "scan": {
            "title": "Test Scan Ios File",
            "assetIds": [ios_file_asset.id],
            "agentGroupId": agent_group_trufflehog.id,
        },
    }

    response = authenticated_flask_client.post(
        "/graphql", json={"query": query, "variables": variables}
    )

    assert response.status_code == 200, response.get_json()
    res_scan = response.get_json()["data"]["runScan"]["scan"]
    assert int(res_scan["id"]) == scan.id
    assert res_scan["title"] == scan.title
    assert res_scan["progress"] == scan.progress.name
    assert len(res_scan["assets"]) == 1
    assert int(res_scan["assets"][0]["id"]) == ios_file_asset.id
    assert "test.ipa" in res_scan["assets"][0]["path"]
    args = scan_mock.call_args[1]
    assert args["title"] == "Test Scan Ios File"
    assert args["agent_group_definition"].agents[0].key == "agent/ostorlab/trufflehog"
    assert len(args["assets"]) == 1
    assert "test.ipa" in args["assets"][0].path


def testRunScanMutation_whenAndroidStore_shouldRunScan(
    authenticated_flask_client: testing.FlaskClient,
    agent_group_inject_asset: models.AgentGroup,
    android_store: models.AndroidStore,
    scan: models.Scan,
    mocker: plugin.MockerFixture,
) -> None:
    """Test RunScanMutation for AndroidStore asset."""
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
    scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan", return_value=scan
    )
    query = """
        mutation RunScan($scan: OxoAgentScanInputType!) {
            runScan(
                scan: $scan
            ) {
                scan {
                    id
                    title
                    progress
                    assets {
                        ... on OxoAndroidStoreAssetType {
                            id
                            packageName
                            applicationName
                        }
                    }
                }
            }
        }
    """
    variables = {
        "scan": {
            "title": "Test Scan Android Store",
            "assetIds": [android_store.id],
            "agentGroupId": agent_group_inject_asset.id,
        },
    }

    response = authenticated_flask_client.post(
        "/graphql", json={"query": query, "variables": variables}
    )

    assert response.status_code == 200, response.get_json()
    res_scan = response.get_json()["data"]["runScan"]["scan"]
    assert int(res_scan["id"]) == scan.id
    assert res_scan["title"] == scan.title
    assert res_scan["progress"] == scan.progress.name
    assert len(res_scan["assets"]) == 1
    assert int(res_scan["assets"][0]["id"]) == android_store.id
    assert res_scan["assets"][0]["packageName"] == "com.example.android"
    args = scan_mock.call_args[1]
    assert args["title"] == "Test Scan Android Store"
    assert args["agent_group_definition"].agents[0].key == "agent/ostorlab/inject_asset"
    assert len(args["assets"]) == 1
    assert "com.example.android" in args["assets"][0].package_name


def testRunScanMutation_whenIosStore_shouldRunScan(
    authenticated_flask_client: testing.FlaskClient,
    agent_group_inject_asset: models.AgentGroup,
    ios_store: models.IosStore,
    scan: models.Scan,
    mocker: plugin.MockerFixture,
) -> None:
    """Test RunScanMutation for IosStore asset."""
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
    scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan", return_value=scan
    )
    query = """
        mutation RunScan($scan: OxoAgentScanInputType!) {
            runScan(
                scan: $scan
            ) {
                scan {
                    id
                    title
                    progress
                    assets {
                        ... on OxoIOSStoreAssetType {
                            id
                            bundleId
                            applicationName
                        }
                    }
                }
            }
        }
    """
    variables = {
        "scan": {
            "title": "Test Scan Ios Store",
            "assetIds": [ios_store.id],
            "agentGroupId": agent_group_inject_asset.id,
        },
    }

    response = authenticated_flask_client.post(
        "/graphql", json={"query": query, "variables": variables}
    )

    assert response.status_code == 200, response.get_json()
    res_scan = response.get_json()["data"]["runScan"]["scan"]
    assert int(res_scan["id"]) == scan.id
    assert res_scan["title"] == scan.title
    assert res_scan["progress"] == scan.progress.name
    assert len(res_scan["assets"]) == 1
    assert int(res_scan["assets"][0]["id"]) == ios_store.id
    assert res_scan["assets"][0]["bundleId"] == "com.example.ios"
    args = scan_mock.call_args[1]
    assert args["title"] == "Test Scan Ios Store"
    assert args["agent_group_definition"].agents[0].key == "agent/ostorlab/inject_asset"
    assert len(args["assets"]) == 1
    assert "com.example.ios" in args["assets"][0].bundle_id


def testRunScanMutation_whenAgentGroupDoesNotExist_returnErrorMessage(
    authenticated_flask_client: testing.FlaskClient,
    android_store: models.AndroidStore,
) -> None:
    """Ensure the run scan mutation returns an error message when the agent group does not exist."""
    query = """
        mutation RunScan($scan: OxoAgentScanInputType!) {
            runScan(
                scan: $scan
            ) {
                scan {
                    id
                    title
                }
            }
        }
    """
    variables = {
        "scan": {
            "title": "Test Scan Android Store",
            "assetIds": [android_store.id],
            "agentGroupId": 999,
        },
    }

    response = authenticated_flask_client.post(
        "/graphql", json={"query": query, "variables": variables}
    )

    assert response.status_code == 200, response.get_json()
    assert response.get_json()["errors"][0]["message"] == "Agent group not found."


def testRunScanMutation_whenAssetDoesNotExist_returnErrorMessage(
    authenticated_flask_client: testing.FlaskClient,
    agent_group_inject_asset: models.AgentGroup,
) -> None:
    """Ensure the run scan mutation returns an error message when the asset does not exist."""
    query = """
        mutation RunScan($scan: OxoAgentScanInputType!) {
            runScan(
                scan: $scan
            ) {
                scan {
                    id
                    title
                }
            }
        }
    """
    variables = {
        "scan": {
            "title": "Test Scan Android Store",
            "assetIds": [999],
            "agentGroupId": agent_group_inject_asset.id,
        },
    }

    response = authenticated_flask_client.post(
        "/graphql", json={"query": query, "variables": variables}
    )

    assert response.status_code == 200, response.get_json()
    assert response.get_json()["errors"][0]["message"] == "Assets not found."


def _get_re_oxo_schema(query: str) -> Dict[str, Any]:
    """Introspect the oxo endpoint on RE, and fetch desired definitions."""

    with httpx.Client(verify=True) as client:
        response = client.post(
            RE_OXO_ENDPOINT,
            data={"query": query},
            timeout=10,
            headers={"X-Api-Key": f"{os.environ.get('RE_OXO_API_KEY', '')}"},
        )

        return response.json()["data"]


@pytest.mark.skip(reason="Schema not complete on RE_OXO.")
def testOxoSchemaReOxoSchemas_whenEnums_schemasShouldBeSimilar() -> None:
    """Ensure the `ENUMs` in the OxO Schema & RE_OxO schema are similar."""

    oxo_schema_dict = oxo_schema.introspect()["__schema"]

    re_oxo_schema_dict = _get_re_oxo_schema(INTROSPECT_ENUMS_QUERY)

    re_oxo_types = re_oxo_schema_dict["__schema"]["types"]

    re_oxo_enums = {}

    for type_definition in re_oxo_types:
        if (
            type_definition["kind"] != "ENUM"
            or type_definition["name"].startswith("__") is True
        ):
            continue

        re_oxo_enums[type_definition["name"]] = {
            enum_value["name"] for enum_value in type_definition["enumValues"]
        }

    oxo_types = oxo_schema_dict["types"]

    oxo_enums = {}

    for type_definition in oxo_types:
        if (
            type_definition["kind"] != "ENUM"
            or type_definition["name"].startswith("__") is True
        ):
            continue

        oxo_enums[type_definition["name"]] = {
            enum_value["name"] for enum_value in type_definition["enumValues"]
        }

    for enum, enum_values in re_oxo_enums.items():
        assert enum in oxo_enums

        assert enum_values == oxo_enums[enum]


@pytest.mark.skip(reason="Schema not complete on RE_OXO.")
def testOxoSchemaReOxoSchemas_whenInputObject_schemasShouldBeSimilar() -> None:
    """Ensure the `InputObjects` in the OxO Schema & RE_OxO schema are similar."""

    oxo_schema_dict = oxo_schema.introspect()["__schema"]
    re_oxo_schema_dict = _get_re_oxo_schema(INTROSPECT_INPUTS_QUERY)
    re_oxo_types = re_oxo_schema_dict["__schema"]["types"]
    re_oxo_inputs = {
        type_definition["name"]: type_definition["inputFields"]
        for type_definition in re_oxo_types
        if type_definition["kind"] == "INPUT_OBJECT"
    }
    oxo_types = oxo_schema_dict["types"]
    oxo_inputs = {
        type_definition["name"]: type_definition["inputFields"]
        for type_definition in oxo_types
        if type_definition["kind"] == "INPUT_OBJECT"
    }
    re_oxo_input_types = {}
    oxo_input_types = {}
    for input_type_name, input_fields in re_oxo_inputs.items():
        assert input_type_name in oxo_inputs

        for input_field in input_fields:
            if input_field["type"]["ofType"] is not None:
                re_oxo_input_types[input_field["name"]] = {
                    "name": input_field["type"]["ofType"]["name"],
                    "kind": input_field["type"]["ofType"]["kind"],
                }

            else:
                re_oxo_input_types[input_field["name"]] = {
                    "name": input_field["type"]["name"],
                    "kind": input_field["type"]["kind"],
                }

        for input_field in oxo_inputs[input_type_name]:
            if input_field["type"]["ofType"] is not None:
                oxo_input_types[input_field["name"]] = {
                    "name": input_field["type"]["ofType"]["name"],
                    "kind": input_field["type"]["ofType"]["kind"],
                }

            else:
                oxo_input_types[input_field["name"]] = {
                    "name": input_field["type"]["name"],
                    "kind": input_field["type"]["kind"],
                }

        for input_field_name, input_field_type in re_oxo_input_types.items():
            assert input_field_name in oxo_input_types
            assert input_field_type == oxo_input_types[input_field_name]


@pytest.mark.skip(reason="Schema not complete on RE_OXO.")
def testOxoSchemaReOxoSchemas_whenMutations_schemasShouldBeSimilar() -> None:
    """Ensure the `Mutations` in the OxO Schema & RE_OxO schema are similar."""

    oxo_schema_dict = oxo_schema.introspect()["__schema"]

    re_oxo_schema_dict = _get_re_oxo_schema(INTROSPECT_MUTATIONS_QUERY)

    re_oxo_types = re_oxo_schema_dict["__schema"]["types"]

    re_oxo_mutation_fields = [
        type_def
        for type_def in re_oxo_types
        if type_def["kind"] == "OBJECT" and type_def["name"] == "Mutations"
    ][0]["fields"]

    re_oxo_mutations = {
        mutation["name"]: mutation for mutation in re_oxo_mutation_fields
    }

    oxo_types = oxo_schema_dict["types"]

    oxo_mutations_fields = [
        type_def
        for type_def in oxo_types
        if type_def["kind"] == "OBJECT" and type_def["name"] == "Mutations"
    ][0]["fields"]

    oxo_mutations = {mutation["name"]: mutation for mutation in oxo_mutations_fields}

    for mutation_name, mutation_fields in re_oxo_mutations.items():
        if mutation_name == "exportScan":
            # This mutation is explicitly skipped from the check.
            # TODO(deadly-panda): Evaluate if exporting scans on oxo is a valid usecase.
            continue
        assert mutation_name in oxo_mutations

        assert mutation_fields["type"] == oxo_mutations[mutation_name]["type"]

        re_oxo_mutation_args = {}

        for arg in mutation_fields["args"]:
            if arg["type"]["ofType"] is not None:
                re_oxo_mutation_args[arg["name"]] = {
                    "name": arg["type"]["ofType"]["name"],
                    "kind": arg["type"]["ofType"]["kind"],
                }

            else:
                re_oxo_mutation_args[arg["name"]] = {
                    "name": arg["type"]["name"],
                    "kind": arg["type"]["kind"],
                }

        oxo_mutation_args = {}

        for arg in oxo_mutations[mutation_name]["args"]:
            if arg["type"]["ofType"] is not None:
                oxo_mutation_args[arg["name"]] = {
                    "name": arg["type"]["ofType"]["name"],
                    "kind": arg["type"]["ofType"]["kind"],
                }

            else:
                oxo_mutation_args[arg["name"]] = {
                    "name": arg["type"]["name"],
                    "kind": arg["type"]["kind"],
                }

        for arg_name, arg_type in re_oxo_mutation_args.items():
            assert arg_name in oxo_mutation_args
            assert arg_type == oxo_mutation_args[arg_name]


@pytest.mark.skip(
    reason="Asset type needs to be aligned (https://github.com/Ostorlab/oxo/pull/713)."
)
def testOxoSchemaReOxoSchemas_whenQueries_schemasShouldBeSimilar() -> None:
    """Ensure the `Queries` in the OxO Schema & RE_OxO schema are similar."""

    oxo_schema_dict = oxo_schema.introspect()["__schema"]
    re_oxo_schema_dict = _get_re_oxo_schema(INTROSPECT_QUERIES_QUERY)
    re_oxo_types = re_oxo_schema_dict["__schema"]["types"]

    re_oxo_query_fields = [
        t for t in re_oxo_types if t["kind"] == "OBJECT" and t["name"] == "Query"
    ][0]["fields"]

    re_oxo_queries = {query["name"]: query for query in re_oxo_query_fields}

    oxo_types = oxo_schema_dict["types"]

    oxo_query_fields = [
        t for t in oxo_types if t["kind"] == "OBJECT" and t["name"] == "Query"
    ][0]["fields"]

    oxo_queries = {query["name"]: query for query in oxo_query_fields}

    for query_name, queriy_fields in re_oxo_queries.items():
        assert query_name in oxo_queries

        assert queriy_fields["type"] == oxo_queries[query_name]["type"]

        re_oxo_query_args = {}

        for arg in queriy_fields["args"]:
            if arg["type"]["ofType"] is not None:
                re_oxo_query_args[arg["name"]] = arg["type"]["ofType"]

            else:
                re_oxo_query_args[arg["name"]] = {
                    "name": arg["type"]["name"],
                    "kind": arg["type"]["kind"],
                }

        oxo_query_args = {}

        for arg in oxo_queries[query_name]["args"]:
            if arg["type"]["ofType"] is not None:
                oxo_query_args[arg["name"]] = arg["type"]["ofType"]

            else:
                oxo_query_args[arg["name"]] = {
                    "name": arg["type"]["name"],
                    "kind": arg["type"]["kind"],
                }

        for arg_name, arg_type in re_oxo_query_args.items():
            assert arg_name in oxo_query_args

            assert arg_type == oxo_query_args[arg_name]


@pytest.mark.skip(reason="Schema not complete on RE_OXO.")
def testOxoSchemaReOxoSchemas_whenUnions_schemasShouldBeSimilar() -> None:
    """Ensure the `UNION` types in the OxO Schema & RE_OxO schema are similar."""

    oxo_schema_dict = oxo_schema.introspect()["__schema"]

    re_oxo_schema_dict = _get_re_oxo_schema(INTROSPECT_UNIONS_QUERY)

    re_oxo_types = re_oxo_schema_dict["__schema"]["types"]

    re_oxo_unions = {}

    for type_definition in re_oxo_types:
        if type_definition["kind"] != "UNION":
            continue

        possible_types = {}

        for possible_type in type_definition["possibleTypes"]:
            field_types = {}

            if possible_type["ofType"] is not None:
                field_types[possible_type["name"]] = possible_type["ofType"]

            else:
                field_types[possible_type["name"]] = {
                    "name": possible_type["name"],
                    "kind": possible_type["kind"],
                }

            possible_types[possible_type["name"]] = field_types

        re_oxo_unions[type_definition["name"]] = possible_types

    oxo_unions = {}

    oxo_types = oxo_schema_dict["types"]

    for type_definition in oxo_types:
        if type_definition["kind"] != "UNION":
            continue

        possible_types = {}

        for possible_type in type_definition["possibleTypes"]:
            field_types = {}

            if possible_type["ofType"] is not None:
                field_types[possible_type["name"]] = possible_type["ofType"]

            else:
                field_types[possible_type["name"]] = {
                    "name": possible_type["name"],
                    "kind": possible_type["kind"],
                }

            possible_types[possible_type["name"]] = field_types

        oxo_unions[type_definition["name"]] = possible_types

    for union_name, union_possible_types in re_oxo_unions.items():
        assert union_name in oxo_unions

        for possible_type_name, possible_type_fields in union_possible_types.items():
            assert possible_type_name in oxo_unions[union_name]

            assert possible_type_fields == oxo_unions[union_name][possible_type_name]


@pytest.mark.skip(reason="Schema not complete on RE_OXO.")
def testOxoSchemaReOxoSchemas_whenOutputTypes_schemasShouldBeSimilar() -> None:
    """Ensure the `return types` in the OxO Schema & RE_OxO schema are similar."""

    oxo_schema_dict = oxo_schema.introspect()["__schema"]
    re_oxo_schema_dict = _get_re_oxo_schema(INTROSPECT_TYPES_QUERY)

    re_oxo_types = re_oxo_schema_dict["__schema"]["types"]
    re_oxo_output_types = {}
    for type_def in re_oxo_types:
        if type_def["kind"] != "OBJECT" or type_def["name"].endswith("Type") is False:
            continue
        fields_types = {}
        for field in type_def["fields"]:
            if field["type"]["ofType"] is not None:
                fields_types[field["name"]] = field["type"]["ofType"]
            else:
                fields_types[field["name"]] = {
                    "name": field["type"]["name"],
                    "kind": field["type"]["kind"],
                }
        re_oxo_output_types[type_def["name"]] = fields_types

    oxo_types = oxo_schema_dict["types"]
    oxo_output_types = {}
    for type_def in oxo_types:
        if type_def["kind"] != "OBJECT" or type_def["name"].endswith("Type") is False:
            continue
        fields_types = {}
        for field in type_def["fields"]:
            if field["type"]["ofType"] is not None:
                fields_types[field["name"]] = {
                    "name": field["type"]["ofType"]["name"],
                    "kind": field["type"]["ofType"]["kind"],
                }
            else:
                fields_types[field["name"]] = {
                    "name": field["type"]["name"],
                    "kind": field["type"]["kind"],
                }
        oxo_output_types[type_def["name"]] = fields_types

    for type_name, fields_types in re_oxo_output_types.items():
        assert type_name in oxo_output_types
        for field_name, field_type in fields_types.items():
            assert field_name in oxo_output_types[type_name]
            assert field_type == oxo_output_types[type_name][field_name]


def testPublishAgentGroup_withoutNameAndAgentArgs_shouldPersistAgentGroup(
    authenticated_flask_client: testing.FlaskClient,
    mocker: plugin.MockerFixture,
    db_engine_path: str,
) -> None:
    """Ensure the publish agent group mutation persists the agent group."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    query = """
        mutation PublishAgentGroup ($agentGroup: OxoAgentGroupCreateInputType!){
            publishAgentGroup (agentGroup: $agentGroup) {
                agentGroup {
                    key
                    name
                    description
                    agents {
                        agents {
                            key
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
        }
    """

    variables = {
        "agentGroup": {
            "description": "agent description",
            "agents": [
                {
                    "key": "agent_key",
                }
            ],
        }
    }

    response = authenticated_flask_client.post(
        "/graphql", json={"query": query, "variables": variables}
    )

    assert response.status_code == 200, response.get_json()
    ag = response.get_json()["data"]["publishAgentGroup"]["agentGroup"]
    assert ag["key"] == "agentgroup//1"
    assert ag["name"] is None
    assert ag["description"] == "agent description"
    assert len(ag["agents"]["agents"]) == 1
    assert ag["agents"]["agents"][0]["key"] == "agent_key"
    assert len(ag["agents"]["agents"][0]["args"]["args"]) == 0


def testQueryAgentGroup_withAgentPagination_shouldReturnPaginatedListOfAgents(
    authenticated_flask_client: testing.FlaskClient,
    agent_group_multiple_agents: models.AgentGroup,
    mocker: plugin.MockerFixture,
    db_engine_path: str,
) -> None:
    """Ensure the query agent group returns a paginated list of agents."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    query = """
        query QueryAgentGroup ($agentGroupIds: [Int!], $page: Int, $numberElements: Int){
            agentGroups (agentGroupIds: $agentGroupIds) {
            agentGroups {
                agents (page: $page, numberElements: $numberElements) {
                    agents {
                        key
                    }
                    pageInfo{
                      count
                      numPages
                      hasNext
                      hasPrevious
                    }
                }
            }
            }
        }
    """
    variables = {
        "agentGroupIds": [agent_group_multiple_agents.id],
        "page": 1,
        "numberElements": 2,
    }

    response = authenticated_flask_client.post(
        "/graphql", json={"query": query, "variables": variables}
    )

    assert response.status_code == 200, response.get_json()
    agents = response.get_json()["data"]["agentGroups"]["agentGroups"][0]["agents"]
    assert len(agents["agents"]) == 2
    assert agents["agents"][0]["key"] == "agent/ostorlab/agent1"
    assert agents["agents"][1]["key"] == "agent/ostorlab/agent2"
    assert agents["pageInfo"]["count"] == 3
    assert agents["pageInfo"]["numPages"] == 2
    assert agents["pageInfo"]["hasNext"] is True
    assert agents["pageInfo"]["hasPrevious"] is False


def testQueryScan_always_shouldReturnScanWithAgentGroup(
    authenticated_flask_client: testing.FlaskClient,
    scan_with_agent_group: models.Scan,
    mocker: plugin.MockerFixture,
    db_engine_path: str,
) -> None:
    """Test query for scan with agent group."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    query = """
        query scan($scanId: Int) {
          scan(scanId:$scanId) {
            id
                agentGroup{
                  id
                  name
                  agents{
                    agents{
                      key
                      args{
                        args{
                          name
                          type
                          value
                        }
                      }
                    }
                  }
                }
            }
        }
    """
    variables = {"scanId": scan_with_agent_group.id}
    ubjson_data = ubjson.dumpb({"query": query, "variables": variables})

    response = authenticated_flask_client.post(
        "/graphql",
        data=ubjson_data,
        headers={"Content-Type": "application/ubjson", "Accept": "application/ubjson"},
    )

    assert response.status_code == 200, ubjson.loadb(response.data)
    data = ubjson.loadb(response.data)["data"]
    assert data["scan"]["id"] == str(scan_with_agent_group.id)
    assert data["scan"]["agentGroup"]["id"] == str(scan_with_agent_group.agent_group_id)
    assert data["scan"]["agentGroup"]["name"] == "Agent Group 1"
    agents = data["scan"]["agentGroup"]["agents"]["agents"]
    assert len(agents) == 2
    assert agents[0]["key"] == "agent/ostorlab/agent1"
    assert len(agents[0]["args"]["args"]) == 1
    assert agents[0]["args"]["args"][0]["name"] == "arg1"
    assert agents[0]["args"]["args"][0]["type"] == "number"
    arg_value = agents[0]["args"]["args"][0]["value"]
    arg_type = agents[0]["args"]["args"][0]["type"]
    assert models.AgentArgument.from_bytes(type=arg_type, value=arg_value) == 42.0
    assert agents[1]["key"] == "agent/ostorlab/agent2"
    assert len(agents[1]["args"]["args"]) == 4
    assert agents[1]["args"]["args"][0]["name"] == "arg2"
    assert agents[1]["args"]["args"][0]["type"] == "string"
    arg_value = agents[1]["args"]["args"][0]["value"]
    arg_type = agents[1]["args"]["args"][0]["type"]
    assert models.AgentArgument.from_bytes(type=arg_type, value=arg_value) == "hello"
    assert agents[1]["args"]["args"][1]["name"] == "arg3"
    assert agents[1]["args"]["args"][1]["type"] == "array"
    arg_value = agents[1]["args"]["args"][1]["value"]
    arg_type = agents[1]["args"]["args"][1]["type"]
    assert models.AgentArgument.from_bytes(type=arg_type, value=arg_value) == [
        "hello",
        "world",
    ]
    assert agents[1]["args"]["args"][2]["name"] == "arg4"
    assert agents[1]["args"]["args"][2]["type"] == "object"
    arg_value = agents[1]["args"]["args"][2]["value"]
    arg_type = agents[1]["args"]["args"][2]["type"]
    assert models.AgentArgument.from_bytes(type=arg_type, value=arg_value) == {
        "hello": "world"
    }
    assert agents[1]["args"]["args"][3]["name"] == "arg5"
    assert agents[1]["args"]["args"][3]["type"] == "boolean"
    arg_value = agents[1]["args"]["args"][3]["value"]
    arg_type = agents[1]["args"]["args"][3]["type"]
    assert models.AgentArgument.from_bytes(type=arg_type, value=arg_value) is False


def testOxoExportScan_alaways_shouldExportScan(
    authenticated_flask_client: testing.FlaskClient,
    android_store_scan: models.Scan,
    mocker: plugin.MockerFixture,
    db_engine_path: str,
) -> None:
    """Test export scan to csv api call."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    query = """
        mutation ExportScan($scanId: Int!) {
            exportScan(scanId: $scanId) {
                content
            }
        }
    """
    variables = {"scanId": android_store_scan.id}
    ubjson_data = ubjson.dumpb({"query": query, "variables": variables})

    response = authenticated_flask_client.post(
        "/graphql",
        data=ubjson_data,
        headers={"Content-Type": "application/ubjson", "Accept": "application/ubjson"},
    )

    assert response.status_code == 200, ubjson.loadb(response.data)
    file_data = ubjson.loadb(response.data)["data"]["exportScan"]["content"]
    with models.Database() as session:
        import_utils.import_scan(file_data=file_data)
        assert session.query(models.Scan).count() == 2
        last_scan = session.query(models.Scan).order_by(models.Scan.id.desc()).first()
        assert last_scan.title == "Android Store Scan"
        assert last_scan.progress == models.ScanProgress.IN_PROGRESS


def testImportScanMutation_whenScanHasMultipleAssets_shouldImportScanWithMultipleAssets(
    authenticated_flask_client: testing.FlaskClient,
    multiple_assets_scan_bytes: bytes,
    mocker: plugin.MockerFixture,
    db_engine_path: str,
) -> None:
    """Test importScan mutation for a scan with multiple assets."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)

    with models.Database() as session:
        nbr_scans_before_import = session.query(models.Scan).count()
        nbr_assets_before_import = session.query(models.Asset).count()
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
        data["file"] = (io.BytesIO(multiple_assets_scan_bytes), file_name)

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
        assert session.query(models.Asset).count() == nbr_assets_before_import + 2
        assets = session.query(models.Asset).all()
        assert assets[0].type == "ios_file"
        assert assets[0].bundle_id == "ostorlab.swiftvulnerableapp"
        assert assets[1].type == "android_store"
        assert assets[1].package_name == "co.banano.natriumwallet"
