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
from pytest_mock import plugin

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
from ostorlab.serve_app import types
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
def web_scan(
    clean_db: None, mocker: plugin.MockerFixture, db_engine_path: str
) -> models.Scan:
    """Create a dummy web scan."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    with models.Database() as session:
        scan = models.Scan(
            title="Web Scan",
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
        models.Urls.create(
            scan_id=scan.id,
            links=[
                {"url": "https://example.com", "method": "GET"},
                {"url": "https://example.com", "method": "POST"},
            ],
        )
        models.ScanStatus.create(
            scan_id=scan.id,
            key="progress",
            value="done",
        )
        return scan


@pytest.fixture
def in_progress_web_scan(clean_db: None) -> models.Scan:
    """Create a dummy web scan."""

    return models.Scan.create(
        title="Web Scan", progress=models.ScanProgress.IN_PROGRESS
    )


@pytest.fixture
def ios_scans(
    clean_db: None, mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Create a dummy ios scan."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)

    with models.Database() as session:
        scan1 = models.Scan(
            title="iOS Scan 1 ",
            progress=models.ScanProgress.DONE,
            created_time=datetime.datetime.now(),
            risk_rating=risk_rating.RiskRating.HIGH,
        )
        scan2 = models.Scan(
            title="iOS Scan 2",
            progress=models.ScanProgress.DONE,
            created_time=datetime.datetime.now(),
            risk_rating=risk_rating.RiskRating.MEDIUM,
        )
        session.add(scan1)
        session.add(scan2)
        session.commit()
        asset1 = models.IosFile(
            bundle_id="com.example.app",
            path="/path/to/file",
            scan_id=scan1.id,
        )
        session.add(asset1)
        session.commit()
        asset2 = models.IosStore(
            bundle_id="com.example.app",
            application_name="Example App",
            scan_id=scan2.id,
        )
        session.add(asset2)
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
def clean_db(mocker: plugin.MockerFixture, db_engine_path: str) -> None:
    """Clean the database."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    with models.Database() as session:
        session.query(models.Vulnerability).delete()
        session.query(models.Scan).delete()
        session.query(models.ScanStatus).delete()
        session.query(models.Agent).delete()
        session.query(models.AgentArgument).delete()
        session.query(models.AgentGroup).delete()
        session.query(models.AgentGroupMapping).delete()
        session.query(models.Asset).delete()
        session.query(models.AndroidFile).delete()
        session.query(models.AndroidStore).delete()
        session.query(models.IosFile).delete()
        session.query(models.IosStore).delete()
        session.query(models.Urls).delete()
        session.query(models.Link).delete()
        session.query(models.Network).delete()
        session.query(models.IPRange).delete()
        session.commit()


@pytest.fixture
def android_scan(
    clean_db: None, mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Create dummy android scan."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    with models.Database() as session:
        scan = models.Scan(
            title="Android Scan 1 ",
            progress=models.ScanProgress.DONE,
            created_time=datetime.datetime.now(),
        )
        session.add(scan)
        session.commit()
        asset = models.AndroidFile(
            package_name="com.example.app",
            path="/path/to/file",
            scan_id=scan.id,
        )
        session.add(asset)
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
def agent_groups(
    clean_db: None, mocker: plugin.MockerFixture, db_engine_path: str
) -> List[models.AgentGroup]:
    """Create dummy agent groups."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
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

        models.AgentArgument.create(
            agent_id=agent1.id, name="arg1", type="number", value=42
        )
        models.AgentArgument.create(
            agent_id=agent2.id, name="arg2", type="string", value="hello"
        )
        models.AgentArgument.create(
            agent_id=agent2.id, name="arg3", type="array", value=["hello", "world"]
        )
        models.AgentArgument.create(
            agent_id=agent2.id, name="arg4", type="object", value={"hello": "world"}
        )
        models.AgentArgument.create(
            agent_id=agent2.id, name="arg5", type="boolean", value=False
        )

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

        asset_ip = models.AssetType.create(type=models.AssetTypeEnum.IP)
        asset_android = models.AssetType.create(type=models.AssetTypeEnum.ANDROID_FILE)
        models.AgentGroupAssetType.create(
            agent_group_id=agent_group1.id, asset_type_id=asset_ip.id
        )
        models.AgentGroupAssetType.create(
            agent_group_id=agent_group2.id, asset_type_id=asset_android.id
        )

        return [agent_group1, agent_group2]


@pytest.fixture
def agent_group(
    clean_db: None, mocker: plugin.MockerFixture, db_engine_path: str
) -> models.AgentGroup:
    """Create dummy agent group."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    with models.Database() as session:
        agent = types.OxoAgentGroupAgentCreateInputType()
        agent.key = "key"
        agent.args = []
        agents = [agent]
        agent_group = models.AgentGroup.create(
            name="Agent Group 1", description="Agent Group 1 description", agents=agents
        )
        session.add(agent_group)
        session.commit()
        return agent_group


@pytest.fixture
def agent_group_multiple_agents(
    clean_db: None, mocker: plugin.MockerFixture, db_engine_path: str
) -> models.AgentGroup:
    """Create dummy agent group."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    with models.Database() as session:
        agent1 = models.Agent.create(
            key="agent/ostorlab/agent1",
        )
        agent2 = models.Agent.create(
            key="agent/ostorlab/agent2",
        )
        agent3 = models.Agent.create(
            key="agent/ostorlab/agent3",
        )
        agent_group = models.AgentGroup(
            name="Agent Group 1",
            description="Agent Group 1 description",
            created_time=datetime.datetime.now(),
        )
        session.add(agent_group)
        session.commit()
        models.AgentGroupMapping.create(
            agent_group_id=agent_group.id, agent_id=agent1.id
        )
        models.AgentGroupMapping.create(
            agent_group_id=agent_group.id, agent_id=agent2.id
        )
        models.AgentGroupMapping.create(
            agent_group_id=agent_group.id, agent_id=agent3.id
        )
        return agent_group


@pytest.fixture
def multiple_assets_scan(
    mocker: plugin.MockerFixture, db_engine_path: str, clean_db: None
) -> models.Scan:
    """Create dummy scan with multiple assets."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    with models.Database() as session:
        scan = models.Scan(
            title="Multiple Assets Scan",
            progress=models.ScanProgress.DONE,
            created_time=datetime.datetime.now(),
            risk_rating=risk_rating.RiskRating.HIGH,
        )
        session.add(scan)
        session.commit()
        models.AndroidFile.create(
            package_name="com.example.app",
            path=str(pathlib.Path(__file__).parent / "files" / "test.apk"),
            scan_id=scan.id,
        )
        models.Network.create(
            networks=[{"host": "8.8.8.8"}, {"host": "8.8.4.4"}],
            scan_id=scan.id,
        )
        models.ScanStatus.create(
            scan_id=scan.id,
            key="progress",
            value="in_progress",
        )
        return scan


@pytest.fixture
def agent_group_nmap(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> models.AgentGroup:
    """Create dummy agent groups."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    with models.Database() as session:
        agent1 = models.Agent(
            key="agent/ostorlab/nmap",
        )
        session.add(agent1)
        session.commit()

        agent_group = models.AgentGroup(
            name="Agent Group Nmap",
            description="Agent Group Nmap",
            created_time=datetime.datetime.now(),
        )
        session.add(agent_group)
        session.commit()

        models.AgentGroupMapping.create(
            agent_group_id=agent_group.id, agent_id=agent1.id
        )
        return agent_group


@pytest.fixture
def agent_group_trufflehog(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> models.AgentGroup:
    """Create dummy agent groups."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    with models.Database() as session:
        agent1 = models.Agent(
            key="agent/ostorlab/trufflehog",
        )
        session.add(agent1)
        session.commit()

        agent_group = models.AgentGroup(
            name="Agent Group Trufflehog",
            description="Agent Group Trufflehog",
            created_time=datetime.datetime.now(),
        )
        session.add(agent_group)
        session.commit()

        models.AgentGroupMapping.create(
            agent_group_id=agent_group.id, agent_id=agent1.id
        )
        return agent_group


@pytest.fixture
def agent_group_inject_asset(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> models.AgentGroup:
    """Create dummy agent groups."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    with models.Database() as session:
        agent1 = models.Agent(
            key="agent/ostorlab/inject_asset",
        )
        session.add(agent1)
        session.commit()

        agent_group = models.AgentGroup(
            name="Agent Group Inject Asset",
            description="Agent Group Inject Asset",
            created_time=datetime.datetime.now(),
        )
        session.add(agent_group)
        session.commit()

        models.AgentGroupMapping.create(
            agent_group_id=agent_group.id, agent_id=agent1.id
        )
        return agent_group


@pytest.fixture
def network_asset(mocker: plugin.MockerFixture, db_engine_path: str) -> models.Network:
    """Create a network asset."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    asset = models.Network.create(
        networks=[{"host": "8.8.8.8"}, {"host": "8.8.4.4", "mask": 24}]
    )
    return asset


@pytest.fixture
def scan(mocker: plugin.MockerFixture, db_engine_path: str) -> models.Scan:
    """Create dummy network scan."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    with models.Database() as session:
        scan = models.Scan(
            title="Scan 1",
            progress=models.ScanProgress.DONE,
            created_time=datetime.datetime.now(),
        )
        session.add(scan)
        session.commit()
        return scan


@pytest.fixture
def scan_with_agent_group(
    db_engine_path: str,
    agent_groups: List[models.AgentGroup],
    clean_db: None,
) -> models.Scan:
    """Create dummy scan with agent group."""
    return models.Scan.create(
        title="Scan with agent group",
        progress=models.ScanProgress.DONE,
        agent_group_id=agent_groups[0].id,
    )


@pytest.fixture
def url_asset(mocker: plugin.MockerFixture, db_engine_path: str) -> models.Urls:
    """Create a Url asset."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    asset = models.Urls.create(
        links=[
            {"url": "https://google.com", "method": "GET"},
            {"url": "https://tesla.com", "method": "GET"},
        ]
    )
    return asset


@pytest.fixture
def domain_asset(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> models.DomainName:
    """Create a DomainName asset."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    asset = models.DomainAsset.create(
        domains=[{"name": "google.com"}, {"name": "tesla.com"}]
    )
    return asset


@pytest.fixture
def android_file_asset(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> models.AndroidFile:
    """Create an AndroidFile asset."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    asset = models.AndroidFile.create(
        package_name="com.example.android",
        path=str(pathlib.Path(__file__).parent / "files" / "test.apk"),
    )
    return asset


@pytest.fixture
def ios_file_asset(mocker: plugin.MockerFixture, db_engine_path: str) -> models.IosFile:
    """Create an IosFile asset."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    asset = models.IosFile.create(
        bundle_id="com.example.ios",
        path=str(pathlib.Path(__file__).parent / "files" / "test.ipa"),
    )
    return asset


@pytest.fixture
def android_store(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> models.AndroidStore:
    """Create an AndroidStore asset."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    asset = models.AndroidStore.create(
        package_name="com.example.android", application_name="Example Android App"
    )
    return asset


@pytest.fixture
def ios_store(mocker: plugin.MockerFixture, db_engine_path: str) -> models.IosStore:
    """Create an IosStore asset."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    asset = models.IosStore.create(
        bundle_id="com.example.ios", application_name="Example iOS App"
    )
    return asset


@pytest.fixture
def nmap_agent_def() -> agent_definitions.AgentDefinition:
    """Create an Nmap agent definition."""
    return agent_definitions.AgentDefinition(
        name="nmap",
        in_selectors=[
            "v3.asset.ip.v4",
            "v3.asset.ip.v6",
            "v3.asset.domain_name",
            "v3.asset.link",
        ],
        out_selectors=["v3.asset.ip.v4.port.service"],
        args=[
            {
                "name": "fast_mode",
                "description": "Fast mode scans fewer ports than the default mode.",
                "type": "boolean",
                "value": True,
            },
            {
                "name": "top_ports",
                "type": "number",
                "description": "Top ports to scan.",
            },
            {
                "name": "timing_template",
                "type": "string",
                "description": "Template of timing settings (T0, T1, ... T5).",
                "value": "T3",
            },
            {
                "name": "scripts",
                "type": "array",
                "description": "List of scripts to run using Nmap",
                "value": ["banner"],
            },
            {
                "name": "float_arg",
                "type": "number",
                "description": "Float argument.",
                "value": 3.14,
            },
        ],
    )


@pytest.fixture
def run_scan_mock(mocker: plugin.MockerFixture) -> None:
    """Mock functions required to run a scan."""
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
    mocker.patch("ostorlab.runtimes.local.runtime.LocalRuntime._create_network")
    mocker.patch("ostorlab.runtimes.local.runtime.LocalRuntime._start_services")
    mocker.patch("ostorlab.runtimes.local.runtime.LocalRuntime._start_pre_agents")
    mocker.patch("ostorlab.runtimes.local.runtime.LocalRuntime._start_post_agents")
    mocker.patch("ostorlab.runtimes.local.runtime.LocalRuntime._start_agents")
    mocker.patch("ostorlab.runtimes.local.runtime.LocalRuntime._check_services_healthy")
    mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime._check_agents_healthy",
        return_value=True,
    )
    mocker.patch("ostorlab.runtimes.local.runtime.LocalRuntime._inject_assets")


@pytest.fixture
def run_scan_mock2(mocker: plugin.MockerFixture) -> None:
    """Mock functions required to run a scan."""
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


@pytest.fixture
def run_scan_mock3(mocker: plugin.MockerFixture) -> None:
    """Mock functions required to run a scan."""
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
    mocker.patch("ostorlab.runtimes.local.runtime.LocalRuntime._create_network")
    mocker.patch("ostorlab.runtimes.local.runtime.LocalRuntime._start_services")
    mocker.patch("ostorlab.runtimes.local.runtime.LocalRuntime._start_pre_agents")
    mocker.patch("ostorlab.runtimes.local.runtime.LocalRuntime._start_agents")
    mocker.patch("ostorlab.runtimes.local.runtime.LocalRuntime._check_services_healthy")
    mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime._check_agents_healthy",
        return_value=True,
    )
    mocker.patch("ostorlab.runtimes.local.runtime.LocalRuntime._inject_assets")


@pytest.fixture
def network_scan(
    clean_db: None, mocker: plugin.MockerFixture, db_engine_path: str
) -> models.Scan:
    """Create a dummy web scan."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    scan = models.Scan.create(
        title="Network Scan",
        progress=models.ScanProgress.IN_PROGRESS,
    )
    models.Vulnerability.create(
        title="XSS",
        short_description="Cross Site Scripting",
        description="Cross Site Scripting",
        recommendation="Sanitize data",
        technical_detail="a=$input",
        risk_rating=risk_rating.RiskRating.HIGH.name,
        cvss_v3_vector="5:6:7",
        dna="121312",
        location={},
        scan_id=scan.id,
        references=[
            {
                "title": "ref",
                "url": "https://url.of.ref",
            }
        ],
    )
    models.Network.create(
        scan_id=scan.id,
        networks=[{"host": "8.8.8.8"}, {"host": "8.8.4.4", "mask": 24}],
    )
    models.ScanStatus.create(
        scan_id=scan.id,
        key="progress",
        value="in_progress",
    )
    return scan


@pytest.fixture
def android_file_scan(
    clean_db: None, mocker: plugin.MockerFixture, db_engine_path: str
) -> models.Scan:
    """Create a dummy android file scan."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    scan = models.Scan.create(
        title="Android File Scan",
        progress=models.ScanProgress.IN_PROGRESS,
    )
    models.Vulnerability.create(
        title="Insecure File Provider Paths Setting",
        short_description="Insecure File Provider Paths Setting",
        description="Insecure File Provider Paths Setting",
        recommendation="some recommendation",
        technical_detail="some technical detail",
        risk_rating=risk_rating.RiskRating.MEDIUM.name,
        cvss_v3_vector="5:6:7",
        dna="121312",
        location={},
        scan_id=scan.id,
        references=[
            {
                "title": "ref",
                "url": "https://url.of.ref",
            }
        ],
    )
    models.AndroidFile.create(
        package_name="com.example.app",
        path=str(pathlib.Path(__file__).parent / "files" / "test.apk"),
        scan_id=scan.id,
    )
    models.ScanStatus.create(
        scan_id=scan.id,
        key="progress",
        value="in_progress",
    )
    return scan


@pytest.fixture
def ios_file_scan(
    clean_db: None, mocker: plugin.MockerFixture, db_engine_path: str
) -> models.Scan:
    """Create a dummy ios file scan."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    scan = models.Scan.create(
        title="IOS File Scan",
        progress=models.ScanProgress.IN_PROGRESS,
    )
    models.Vulnerability.create(
        title="Insecure App Transport Security (ATS) Settings",
        short_description="Insecure App Transport Security (ATS) Settings",
        description="Insecure App Transport Security (ATS) Settings",
        recommendation="some recommendation",
        technical_detail="some technical detail",
        risk_rating=risk_rating.RiskRating.MEDIUM.name,
        cvss_v3_vector="5:6:7",
        dna="121312",
        location={},
        scan_id=scan.id,
        references=[
            {
                "title": "ref",
                "url": "https://url.of.ref",
            }
        ],
    )
    models.IosFile.create(
        bundle_id="com.example.app",
        path=str(pathlib.Path(__file__).parent / "files" / "test.ipa"),
        scan_id=scan.id,
    )
    models.ScanStatus.create(
        scan_id=scan.id,
        key="progress",
        value="in_progress",
    )
    return scan


@pytest.fixture
def ios_store_scan(
    clean_db: None, mocker: plugin.MockerFixture, db_engine_path: str
) -> models.Scan:
    """Create a dummy ios store scan."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    scan = models.Scan.create(
        title="IOS Store Scan",
        progress=models.ScanProgress.IN_PROGRESS,
    )
    models.Vulnerability.create(
        title="Insecure App Transport Security (ATS) Settings",
        short_description="Insecure App Transport Security (ATS) Settings",
        description="Insecure App Transport Security (ATS) Settings",
        recommendation="some recommendation",
        technical_detail="some technical detail",
        risk_rating=risk_rating.RiskRating.MEDIUM.name,
        cvss_v3_vector="5:6:7",
        dna="121312",
        location={},
        scan_id=scan.id,
        references=[
            {
                "title": "ref",
                "url": "https://url.of.ref",
            }
        ],
    )
    models.IosStore.create(
        bundle_id="com.example.app",
        application_name="Example App",
        scan_id=scan.id,
    )
    models.ScanStatus.create(
        scan_id=scan.id,
        key="progress",
        value="in_progress",
    )
    return scan


@pytest.fixture
def android_store_scan(
    clean_db: None, mocker: plugin.MockerFixture, db_engine_path: str
) -> models.Scan:
    """Create a dummy android store scan."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    scan = models.Scan.create(
        title="Android Store Scan",
        progress=models.ScanProgress.IN_PROGRESS,
    )
    models.Vulnerability.create(
        title="Insecure File Provider Paths Setting",
        short_description="Insecure File Provider Paths Setting",
        description="Insecure File Provider Paths Setting",
        recommendation="some recommendation",
        technical_detail="some technical detail",
        risk_rating=risk_rating.RiskRating.MEDIUM.name,
        cvss_v3_vector="5:6:7",
        dna="121312",
        location={},
        scan_id=scan.id,
        references=[
            {
                "title": "ref",
                "url": "https://url.of.ref",
            }
        ],
    )
    models.AndroidStore.create(
        package_name="com.example.app",
        application_name="Example App",
        scan_id=scan.id,
    )
    models.ScanStatus.create(
        scan_id=scan.id,
        key="progress",
        value="in_progress",
    )
    return scan


@pytest.fixture
def multiple_assets_scan_bytes() -> bytes:
    """Returns a dummy zip file."""
    zip_path = pathlib.Path(__file__).parent / "files" / "multiple_assets_scan.zip"
    return zip_path.read_bytes()


@pytest.fixture
def scan_multiple_vulnz_different_risk_ratings(
    clean_db: None, mocker: plugin.MockerFixture, db_engine_path: str
) -> models.Scan:
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    create_scan_db = models.Scan.create("test")
    models.Vulnerability.create(
        title="vulnerability 1",
        short_description="vulnerability 1",
        description="vulnerability 1",
        recommendation="Consider fixing soon",
        technical_detail="example=$input",
        risk_rating="MEDIUM",
        cvss_v3_vector="5:6:7",
        dna="12347",
        location={},
        scan_id=create_scan_db.id,
        references=[],
    )
    models.Vulnerability.create(
        title="vulnerability 2",
        short_description="vulnerability 2",
        description="vulnerability 2",
        recommendation="Fix immediately",
        technical_detail="example=$input",
        risk_rating="HIGH",
        cvss_v3_vector="5:6:7",
        dna="12345",
        location={},
        scan_id=create_scan_db.id,
        references=[],
    )
    models.Vulnerability.create(
        title="vulnerability 3",
        short_description="vulnerability 3",
        description="vulnerability 3",
        recommendation="Monitor the situation",
        technical_detail="example=$input",
        risk_rating="LOW",
        cvss_v3_vector="5:6:7",
        dna="12346",
        location={},
        scan_id=create_scan_db.id,
        references=[],
    )
    models.Vulnerability.create(
        title="vulnerability 4",
        short_description="vulnerability 4",
        description="vulnerability 4",
        recommendation="Consider fixing soon",
        technical_detail="example=$input",
        risk_rating="MEDIUM",
        cvss_v3_vector="5:6:7",
        dna="12347",
        location={},
        scan_id=create_scan_db.id,
        references=[],
    )
    return create_scan_db


@pytest.fixture
def call_trace() -> agent_report_vulnerability_mixin.CallTrace:
    frame1 = agent_report_vulnerability_mixin.Frame(
        function_name="test_func1",
        class_name="TestClass1",
        package_name="test.package1",
    )
    frame2 = agent_report_vulnerability_mixin.Frame(
        function_name="test_func2",
        class_name="TestClass2",
        package_name="test.package2",
    )

    return agent_report_vulnerability_mixin.CallTrace(
        frames=[frame1, frame2],
    )
