"""Definitions of the fixtures that will be shared among multiple tests."""

import datetime
import io
import pathlib
import sys
import time
from typing import Any, List

import docker
import flask
import pytest
import redis
from docker.models import networks as networks_model
from flask import testing as flask_testing
from werkzeug import test as werkzeug_test

import ostorlab
from ostorlab.agent import definitions as agent_definitions
from ostorlab.agent.message import message as agent_message
from ostorlab.agent.mixins import agent_report_vulnerability_mixin
from ostorlab.assets import android_aab as android_aab_asset
from ostorlab.assets import android_apk as android_apk_asset
from ostorlab.assets import android_store as android_store_asset
from ostorlab.assets import domain_name as domain_name_asset
from ostorlab.assets import file as file_asset
from ostorlab.assets import ios_ipa as ios_ipa_asset
from ostorlab.assets import ios_store as ios_store_asset
from ostorlab.assets import ipv4 as ipv4_asset
from ostorlab.assets import ipv6 as ipv6_asset
from ostorlab.assets import link as link_asset
from ostorlab.runtimes.local.models import models
from ostorlab.runtimes.local.services import mq
from ostorlab.runtimes.local.services import redis as local_redis_service
from ostorlab.scanner import scanner_conf
from ostorlab.scanner.proto.assets import apk_pb2
from ostorlab.scanner.proto.scan._location import startAgentScan_pb2
from ostorlab.serve_app import app
from ostorlab.utils import risk_rating


@pytest.fixture(scope="session")
def mq_service():
    """Start MQ Docker service"""
    lrm = mq.LocalRabbitMQ(
        name="core_mq", network="test_network", exposed_ports={5672: 5672, 15672: 15672}
    )
    lrm.start()
    lrm.is_service_healthy()
    yield lrm
    lrm.stop()


@pytest.fixture(scope="session")
def redis_service():
    """Start Redis Docker service"""
    lr = local_redis_service.LocalRedis(
        name="core_redis", network="test_network", exposed_ports={6379: 6379}
    )
    lr.start()
    time.sleep(3)
    yield lr
    lr.stop()


@pytest.fixture
def json_schema_file() -> io.StringIO:
    """Json schema is made a fixture since it will be used by multiple unit tests.

    Returns:
      json_schema_file_object : a file object of the json schema file.

    """
    json_schema = """
        {
            "CustomTypes": {
                "ArrayOfStrings": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "maxLength": 4096
                    }
                }
            },
            "properties": {
                "name": {
                    "type": "string",
                    "maxLength": 2048
                },
                "description":{
                    "type": "string"
                },
                "image":{
                    "type": "string",
                    "pattern": "((?:[^/]*/)*)(.*)"
                },
                "source":{
                    "type": "string",
                    "format": "uri",
                    "pattern": "^https?://",
                    "maxLength": 4096
                },
                "license":{
                    "type": "string",
                    "maxLength": 1024
                },
                "durability":{
                    "type": "string",
                    "enum": ["temporary", "development", "published"]
                },
                "restrictions": {
                    "$ref": "#/CustomTypes/ArrayOfStrings"
                },

                "in_selectors":{
                    "$ref": "#/CustomTypes/ArrayOfStrings"
                },

                "out_selectors":{
                    "$ref": "#/CustomTypes/ArrayOfStrings"
                },
                "restart_policy":{
                    "type": "string",
                    "enum": ["any", "on-failure", "none"]
                },
                "constraints":{
                    "$ref": "#/CustomTypes/ArrayOfStrings"
                },
                "mounts":{
                    "$ref": "#/CustomTypes/ArrayOfStrings"
                },
                "mem_limit":{
                    "type": "number"
                },
                "args": {
                    "description": "[Optional] - Array of dictionary-like objects, defining the agent arguments.",
                    "type": "array",
                    "items": {
                        "description": "Dictionary-like object of the argument.",
                        "type": "object",
                        "properties": {
                            "name": {
                                "description": "[Required] - Name of the agent argument.",
                                "type": "string",
                                "maxLength": 2048
                            },
                            "type": {
                                "description": "[Required] - Type of the agent argument : respecting the jsonschema types.",
                                "type": "string",
                                "maxLength": 2048
                            }
                        },
                        "required": ["name", "type"]
                    }
                }
            },
            "required": ["name", "image", "source", "durability", "restrictions", "in_selectors", "out_selectors", "restart_policy", "args"]
        }

    """
    json_schema_file_object = io.StringIO(json_schema)
    return json_schema_file_object


@pytest.fixture
def agent_group_json_schema_file() -> io.StringIO:
    """Agent group json schema is made a fixture since it will be used by multiple unit tests.

    Returns:
      json_schema_file_object : a file object of the agent group json schema file.

    """
    json_schema = """
        {
            "CustomTypes": {
                "agentArgument": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "maxLength": 2048
                        },
                        "type": {
                            "type": "string",
                            "maxLength": 2048
                        }
                    },
                    "required": ["name", "type"]
                }
            },
            "properties": {
                "description":{
                    "type": "string"
                },
                "kind":{
                    "type": "string",
                    "enum": [
                        "AgentGroup"
                    ]
                },
                "agents": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "key": {
                                "type": "string"
                            },
                            "args": {
                                "type": "array",
                                "items": {
                                    "$ref": "#/CustomTypes/agentArgument"
                                },
                                "default": []
                            }
                        },
                        "required": ["key", "args"]
                    }
                }
            },
            "required": ["kind", "description", "agents"]
        }

    """
    json_schema_file_object = io.StringIO(json_schema)
    return json_schema_file_object


@pytest.fixture()
def image_cleanup(request):
    """Pytest fixture for removing docker image with a specified tag."""
    client = docker.from_env()
    yield client
    tag = request.param
    for img in client.images.list():
        for t in img.tags:
            if tag in t:
                client.images.remove(t)


@pytest.fixture(name="db_engine_path")
def local_db_engine_path(tmpdir):
    if sys.platform == "win32":
        path = f"sqlite:///{tmpdir}\\ostorlab_db1.sqlite".replace("\\", "\\\\")
    else:
        path = f"sqlite:////{tmpdir}/ostorlab_db1.sqlite"
    return path


@pytest.fixture()
def clean_redis_data(request) -> None:
    """Clean all redis data."""
    yield
    redis_url = request.param
    redis_client = redis.Redis.from_url(redis_url)
    keys = redis_client.keys()
    for key in keys:
        redis_client.delete(key)


@pytest.fixture(name="metadata_file_path")
def fixture_metadata_file_path():
    return agent_report_vulnerability_mixin.VulnerabilityLocationMetadata(
        metadata_type=agent_report_vulnerability_mixin.MetadataType.FILE_PATH,
        value="/home/etc",
    )


@pytest.fixture(name="metadata_code_location")
def fixture_metadata_code_location():
    return agent_report_vulnerability_mixin.VulnerabilityLocationMetadata(
        metadata_type=agent_report_vulnerability_mixin.MetadataType.CODE_LOCATION,
        value="config.xml:15",
    )


@pytest.fixture(name="metadata_url")
def fixture_metadata_url():
    return agent_report_vulnerability_mixin.VulnerabilityLocationMetadata(
        metadata_type=agent_report_vulnerability_mixin.MetadataType.URL,
        value="https://example.com/product=15",
    )


@pytest.fixture(name="metadata_port")
def fixture_metadata_port():
    return agent_report_vulnerability_mixin.VulnerabilityLocationMetadata(
        metadata_type=agent_report_vulnerability_mixin.MetadataType.PORT, value="23"
    )


@pytest.fixture()
def vulnerability_location_android_aab(
    metadata_file_path, metadata_code_location, metadata_port, metadata_url
):
    return agent_report_vulnerability_mixin.VulnerabilityLocation(
        metadata=[
            metadata_file_path,
            metadata_code_location,
            metadata_port,
            metadata_url,
        ],
        asset=android_aab_asset.AndroidAab(content=b"aab"),
    )


@pytest.fixture()
def vulnerability_location_android_apk(
    metadata_file_path, metadata_code_location, metadata_port, metadata_url
):
    return agent_report_vulnerability_mixin.VulnerabilityLocation(
        metadata=[
            metadata_file_path,
            metadata_code_location,
            metadata_port,
            metadata_url,
        ],
        asset=android_apk_asset.AndroidApk(content=b"apk"),
    )


@pytest.fixture()
def vulnerability_location_android_store(
    metadata_file_path, metadata_code_location, metadata_port, metadata_url
):
    return agent_report_vulnerability_mixin.VulnerabilityLocation(
        metadata=[
            metadata_file_path,
            metadata_code_location,
            metadata_port,
            metadata_url,
        ],
        asset=android_store_asset.AndroidStore(package_name="a.b.c"),
    )


@pytest.fixture()
def vulnerability_location_ios_store(
    metadata_file_path, metadata_code_location, metadata_port, metadata_url
):
    return agent_report_vulnerability_mixin.VulnerabilityLocation(
        metadata=[
            metadata_file_path,
            metadata_code_location,
            metadata_port,
            metadata_url,
        ],
        asset=ios_store_asset.IOSStore(bundle_id="a.b.c"),
    )


@pytest.fixture()
def vulnerability_location_ios_ipa(
    metadata_file_path, metadata_code_location, metadata_port, metadata_url
):
    return agent_report_vulnerability_mixin.VulnerabilityLocation(
        metadata=[
            metadata_file_path,
            metadata_code_location,
            metadata_port,
            metadata_url,
        ],
        asset=ios_ipa_asset.IOSIpa(content=b"a.b.c"),
    )


@pytest.fixture()
def vulnerability_location_link_asset(
    metadata_file_path, metadata_code_location, metadata_port, metadata_url
):
    return agent_report_vulnerability_mixin.VulnerabilityLocation(
        metadata=[
            metadata_file_path,
            metadata_code_location,
            metadata_port,
            metadata_url,
        ],
        asset=link_asset.Link(url="https://example.com", method="GET"),
    )


@pytest.fixture()
def vulnerability_location_ipv4(
    metadata_file_path, metadata_code_location, metadata_port, metadata_url
):
    return agent_report_vulnerability_mixin.VulnerabilityLocation(
        metadata=[
            metadata_file_path,
            metadata_code_location,
            metadata_port,
            metadata_url,
        ],
        asset=ipv4_asset.IPv4(host="8.8.8.8"),
    )


@pytest.fixture()
def vulnerability_location_ipv6(
    metadata_file_path, metadata_code_location, metadata_port, metadata_url
):
    return agent_report_vulnerability_mixin.VulnerabilityLocation(
        metadata=[
            metadata_file_path,
            metadata_code_location,
            metadata_port,
            metadata_url,
        ],
        asset=ipv6_asset.IPv6(host="2001:4860:4860::8888"),
    )


@pytest.fixture()
def vulnerability_location_domain_name(
    metadata_file_path, metadata_code_location, metadata_port, metadata_url
):
    return agent_report_vulnerability_mixin.VulnerabilityLocation(
        metadata=[
            metadata_file_path,
            metadata_code_location,
            metadata_port,
            metadata_url,
        ],
        asset=domain_name_asset.DomainName(name="ostorlab.co"),
    )


@pytest.fixture()
def vulnerability_location_file(
    metadata_file_path, metadata_code_location, metadata_port, metadata_url
):
    return agent_report_vulnerability_mixin.VulnerabilityLocation(
        metadata=[
            metadata_file_path,
            metadata_code_location,
            metadata_port,
            metadata_url,
        ],
        asset=file_asset.File(content=b"file"),
    )


@pytest.fixture()
def data_start_agent_scan() -> dict[str, Any]:
    return {
        "data": {
            "scanners": {
                "scanners": [
                    {
                        "id": "1",
                        "name": "5485",
                        "uuid": "a1ffcc25-3aa2-4468-ba8f-013d17acb443",
                        "description": "dsqd",
                        "config": {
                            "busUrl": "nats://nats.nats",
                            "busClusterId": "cluster_id",
                            "busClientName": "bus_name",
                            "subjectBusConfigs": {
                                "subjectBusConfigs": [
                                    {"subject": "scan.startAgentScan", "queue": "1"},
                                ]
                            },
                        },
                    }
                ]
            }
        }
    }


@pytest.fixture()
def data_list_agent() -> dict[str, Any]:
    return {"data": {"agent": {"versions": {"versions": [{"version": "0.0.1"}]}}}}


@pytest.fixture()
def data_create_agent_group() -> dict[str, Any]:
    return {"data": {"publishAgentGroup": {"agentGroup": {"id": "1"}}}}


@pytest.fixture()
def data_create_asset() -> dict[str, Any]:
    return {"data": {"createAsset": {"asset": {"id": "1"}}}}


@pytest.fixture()
def start_agent_scan_nats_request() -> startAgentScan_pb2.Message:
    message = startAgentScan_pb2.Message(
        reference_scan_id=42,
        key="agentgroup/ostorlab/agent_group42",
        agents=[
            startAgentScan_pb2.Agent(
                key="agent/ostorlab/agent1",
                version="0.0.1",
                replicas=42,
                args=[startAgentScan_pb2.Arg(name="arg1", type="number", value=b"42")],
            ),
            startAgentScan_pb2.Agent(
                key="agent/ostorlab/agent2", version="0.0.2", replicas=1, args=[]
            ),
        ],
        apk=apk_pb2.Message(content=b"dummy_apk"),
    )
    return message


@pytest.fixture
def local_runtime_mocks(mocker, db_engine_path):
    def docker_networks():
        """Method for mocking docker network list."""
        return [networks_model.Network(attrs={"name": "ostorlab_local_network_1"})]

    mocker.patch(
        "docker.DockerClient.networks", return_value=networks_model.NetworkCollection()
    )
    mocker.patch("docker.DockerClient.networks.list", side_effect=docker_networks)
    mocker.patch.object(
        ostorlab.runtimes.local.models.models, "ENGINE_URL", db_engine_path
    )
    mocker.patch(
        "ostorlab.runtimes.local.services.mq.LocalRabbitMQ.start", return_value=None
    )
    mocker.patch(
        "ostorlab.runtimes.local.services.mq.LocalRabbitMQ.is_healthy",
        return_value=True,
    )
    mocker.patch(
        "ostorlab.runtimes.local.services.redis.LocalRedis.start", return_value=None
    )
    mocker.patch(
        "ostorlab.runtimes.local.services.redis.LocalRedis.is_healthy",
        return_value=True,
    )
    mocker.patch(
        "ostorlab.runtimes.local.agent_runtime.AgentRuntime.create_agent_service"
    )


@pytest.fixture
def apk_start_agent_scan_bus_msg() -> startAgentScan_pb2.Message:
    return startAgentScan_pb2.Message(
        reference_scan_id=42,
        key="agentgroup/ostorlab/agent_group42",
        agents=[
            startAgentScan_pb2.Agent(
                key="agent/ostorlab/agent1",
                args=[startAgentScan_pb2.Arg(name="arg1", type="number", value=b"42")],
            ),
        ],
        apk=apk_pb2.Message(content=b"dummy_apk"),
    )


@pytest.fixture
def ping_message() -> agent_message.Message:
    return agent_message.Message.from_data(
        "v3.healthcheck.ping",
        {
            "body": "Hello, can you hear me?",
        },
    )


@pytest.fixture
def registry_conf() -> scanner_conf.RegistryConfig:
    return scanner_conf.RegistryConfig(username="username", token="token", url="url")


@pytest.fixture
def nmap_agent_definition() -> agent_definitions.AgentDefinition:
    """Returns a dummy agent definition for nmap agent."""
    return agent_definitions.AgentDefinition(
        name="nmap",
        args=[
            {"name": "fast_mode", "type": "boolean", "value": None},
            {"name": "scripts", "type": "array", "value": None},
        ],
    )


@pytest.fixture
def zip_file_bytes() -> bytes:
    """Returns a dummy zip file."""
    zip_path = pathlib.Path(__file__).parent / "files" / "exported_scan_re.zip"
    return zip_path.read_bytes()


@pytest.fixture
def web_scan(clean_db: None) -> None:
    """Create a dummy web scan."""
    with models.Database() as session:
        scan = models.Scan(
            title="Web Scan",
            asset="Web",
            progress=models.ScanProgress.DONE,
            created_time=datetime.datetime.now(),
        )
        session.add(scan)
        session.commit()
        vulnerability = models.Vulnerability(
            title="XSS",
            short_description="Cross Site Scripting",
            description="Cross Site Scripting",
            recommendation="Sanitize data",
            technical_detail="a=$input",
            risk_rating=risk_rating.RiskRating.HIGH,
            cvss_v3_vector="5:6:7",
            dna="121312",
            location="",
            scan_id=scan.id,
        )
        session.add(vulnerability)
        session.commit()


@pytest.fixture
def in_progress_web_scan(clean_db: None) -> models.Scan:
    """Create a dummy web scan."""

    return models.Scan.create(
        title="Web Scan", asset="Web", progress=models.ScanProgress.IN_PROGRESS
    )


@pytest.fixture
def ios_scans(clean_db: None) -> None:
    """Create a dummy ios scan."""
    with models.Database() as session:
        scan1 = models.Scan(
            title="iOS Scan 1 ",
            asset="iOS",
            progress=models.ScanProgress.DONE,
            created_time=datetime.datetime.now(),
        )
        scan2 = models.Scan(
            title="iOS Scan 2",
            asset="iOS",
            progress=models.ScanProgress.DONE,
            created_time=datetime.datetime.now(),
        )
        session.add(scan1)
        session.add(scan2)
        session.commit()
        vulnerability1 = models.Vulnerability.create(
            title="XSS",
            short_description="Cross Site Scripting",
            description="Cross Site Scripting",
            recommendation="Sanitize data",
            technical_detail="a=$input",
            risk_rating=risk_rating.RiskRating.HIGH.name,
            cvss_v3_vector="5:6:7",
            dna="121312",
            location={},
            scan_id=scan1.id,
            references=[
                {
                    "title": "C++ Core Guidelines R.10 - Avoid malloc() and free()",
                    "url": "https://github.com/isocpp/CppCoreGuidelines/blob/036324/CppCoreGuidelines.md#r10-avoid-malloc-and-free",
                }
            ],
        )
        vulnerability2 = models.Vulnerability.create(
            title="SQL Injection",
            short_description="SQL Injection",
            description="SQL Injection",
            recommendation="Sanitize data",
            technical_detail="a=$input",
            risk_rating=risk_rating.RiskRating.HIGH.name,
            cvss_v3_vector="5:6:7",
            dna="121312",
            location={},
            scan_id=scan2.id,
            references=[
                {
                    "title": "C++ Core Guidelines R.10 - Avoid malloc() and free()",
                    "url": "https://github.com/isocpp/CppCoreGuidelines/blob/036324/CppCoreGuidelines.md#r10-avoid-malloc-and-free",
                }
            ],
        )
        session.add(vulnerability1)
        session.add(vulnerability2)
        session.commit()


@pytest.fixture
def flask_app() -> flask.Flask:
    """Fixture for creating a Flask app."""
    flask_app = app.create_app()

    ctx = flask_app.app_context()
    ctx.push()
    return flask_app


@pytest.fixture
def unauthenticated_flask_client(flask_app: flask.Flask) -> flask_testing.FlaskClient:
    """Fixture for creating an unauthenticated Flask test client."""
    return flask_app.test_client()


@pytest.fixture
def authenticated_flask_client(flask_app: flask.Flask) -> flask_testing.FlaskClient:
    """Fixture for creating an authenticated Flask test client."""

    class CustomFlaskClient(flask_testing.FlaskClient):
        def open(self, *args: Any, **kwargs: Any) -> werkzeug_test.TestResponse:
            headers = kwargs.pop("headers", {})
            headers["X-API-Key"] = models.APIKey.get_or_create().key
            kwargs["headers"] = headers
            return super().open(*args, **kwargs)

    flask_app.test_client_class = CustomFlaskClient
    return flask_app.test_client()


@pytest.fixture
def clean_db(request) -> None:
    """Clean the database."""
    with models.Database() as session:
        session.query(models.Vulnerability).delete()
        session.query(models.Scan).delete()
        session.query(models.ScanStatus).delete()
        session.query(models.Agent).delete()
        session.query(models.AgentArgument).delete()
        session.query(models.AgentGroup).delete()
        session.query(models.AgentGroupMapping).delete()
        session.commit()


@pytest.fixture
def android_scan(clean_db: None) -> None:
    """Create dummy android scan."""
    with models.Database() as session:
        scan = models.Scan(
            title="Android Scan 1 ",
            asset="Android file",
            progress=models.ScanProgress.DONE,
            created_time=datetime.datetime.now(),
        )
        session.add(scan)
        session.commit()
        scan_status = models.ScanStatus(
            created_time=datetime.datetime.now(),
            key="dummy-key",
            value="dummy-value",
            scan_id=scan.id,
        )
        session.add(scan_status)
        session.commit()
        vulnerability1 = models.Vulnerability(
            title="XSS",
            short_description="Cross Site Scripting",
            description="Cross Site Scripting",
            recommendation="Sanitize data",
            technical_detail="a=$input",
            risk_rating=risk_rating.RiskRating.LOW,
            cvss_v3_vector="5:6:7",
            dna="121312",
            location="",
            scan_id=scan.id,
        )
        vulnerability2 = models.Vulnerability(
            title="SQL Injection",
            short_description="SQL Injection",
            description="SQL Injection",
            recommendation="Sanitize data",
            technical_detail="a=$input",
            risk_rating=risk_rating.RiskRating.HIGH,
            cvss_v3_vector="5:6:7",
            dna="121312",
            location="",
            scan_id=scan.id,
        )
        vulnerability3 = models.Vulnerability(
            title="SQL Injection",
            short_description="SQL Injection",
            description="SQL Injection",
            recommendation="Sanitize data",
            technical_detail="a=$input",
            risk_rating=risk_rating.RiskRating.MEDIUM,
            cvss_v3_vector="5:6:7",
            dna="121312",
            location="",
            scan_id=scan.id,
        )
        vulnerability4 = models.Vulnerability(
            title="SQL Injection",
            short_description="SQL Injection",
            description="SQL Injection",
            recommendation="Sanitize data",
            technical_detail="a=$input",
            risk_rating=risk_rating.RiskRating.CRITICAL,
            cvss_v3_vector="5:6:7",
            dna="121312",
            location="",
            scan_id=scan.id,
        )
        session.add(vulnerability1)
        session.add(vulnerability2)
        session.add(vulnerability3)
        session.add(vulnerability4)
        session.commit()
    yield scan


@pytest.fixture
def agent_groups(clean_db: None) -> List[models.AgentGroup]:
    """Create dummy agent groups."""
    with models.Database() as session:
        agent1 = models.Agent(
            key="agent/ostorlab/agent1",
        )
        agent2 = models.Agent(
            key="agent/ostorlab/agent2",
        )
        session.add(agent1)
        session.add(agent2)
        session.commit()

        arg1 = models.AgentArgument(
            agent_id=agent1.id, name="arg1", type="number", value="42"
        )
        arg2 = models.AgentArgument(
            agent_id=agent2.id, name="arg2", type="string", value="hello"
        )
        session.add(arg1)
        session.add(arg2)
        session.commit()

        agent_group1 = models.AgentGroup(
            name="Agent Group 1",
            description="Agent Group 1",
            created_time=datetime.datetime(2024, 5, 30, 12, 0, 0),
        )
        agent_group2 = models.AgentGroup(
            name="Agent Group 2",
            description="Agent Group 2",
            created_time=datetime.datetime(2024, 5, 30, 12, 0, 0),
        )
        session.add(agent_group1)
        session.add(agent_group2)
        session.commit()

        models.AgentGroupMapping.create(
            agent_group_id=agent_group1.id, agent_id=agent1.id
        )
        models.AgentGroupMapping.create(
            agent_group_id=agent_group1.id, agent_id=agent2.id
        )
        models.AgentGroupMapping.create(
            agent_group_id=agent_group2.id, agent_id=agent1.id
        )
        return [agent_group1, agent_group2]


@pytest.fixture
def agent_group(clean_db: None) -> models.AgentGroup:
    """Create dummy agent groups."""
    with models.Database() as session:
        agent1 = models.Agent(
            key="agent/ostorlab/agent1",
        )
        agent2 = models.Agent(
            key="agent/ostorlab/agent2",
        )
        session.add(agent1)
        session.add(agent2)
        session.commit()

        arg1 = models.AgentArgument(
            agent_id=agent1.id, name="arg1", type="number", value="42"
        )
        arg2 = models.AgentArgument(
            agent_id=agent2.id, name="arg2", type="string", value="hello"
        )
        session.add(arg1)
        session.add(arg2)
        session.commit()

        agent_group = models.AgentGroup(
            name="Agent Group 1",
            description="Agent Group 1",
            created_time=datetime.datetime(2024, 5, 30, 12, 0, 0),
        )
        session.add(agent_group)
        session.commit()

        models.AgentGroupMapping.create(
            agent_group_id=agent_group.id, agent_id=agent1.id
        )
        models.AgentGroupMapping.create(
            agent_group_id=agent_group.id, agent_id=agent2.id
        )

        return agent_group
