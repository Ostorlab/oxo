"""Tests for Models class."""

from pytest_mock import plugin

from ostorlab.runtimes.local.models import models
from ostorlab.utils import risk_rating


def testModels_whenDatabaseDoesNotExist_DatabaseAndScanCreated(mocker, db_engine_path):
    """Test when database does not exists, scan is populated in a newly created database."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    models.Scan.create(title="test", asset="Asset")

    with models.Database() as session:
        assert session.query(models.Scan).count() == 1
        assert session.query(models.Scan).all()[0].title == "test"


def testScanUpdate_always_updatesExistingScan(mocker, db_engine_path):
    """Test Agent save implementation."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    models.Scan.create("test")

    with models.Database() as session:
        assert session.query(models.Scan).count() == 1
        scan = session.query(models.Scan).first()
        scan.title = "test2"
        session.commit()

        assert session.query(models.Scan).count() == 1
        scan = session.query(models.Scan).first()
        assert scan.title == "test2"


def testModelsVulnerability_whenDatabaseDoesNotExist_DatabaseAndScanCreated(
    mocker, db_engine_path
):
    """Test Vulnerability Model implementation."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    create_scan_db = models.Scan.create("test")
    with models.Database() as session:
        init_count = session.query(models.Vulnerability).count()
    models.Vulnerability.create(
        title="MyVuln",
        short_description="Xss",
        description="Javascript Vuln",
        recommendation="Sanitize data",
        technical_detail="a=$input",
        risk_rating="HIGH",
        cvss_v3_vector="5:6:7",
        dna="121312",
        location={
            "ios_store": {"bundle_id": "some.dummy.bundle"},
            "metadata": [{"type": "CODE_LOCATION", "value": "some/file.swift:42"}],
        },
        scan_id=create_scan_db.id,
    )

    with models.Database() as session:
        assert session.query(models.Vulnerability).count() == init_count + 1
        assert session.query(models.Vulnerability).all()[0].title == "MyVuln"
        assert session.query(models.Vulnerability).all()[0].scan_id == create_scan_db.id
        assert (
            "iOS: `some.dummy.bundle`"
            in session.query(models.Vulnerability).all()[0].location
        )


def testModelsVulnerability_whenAssetIsNotSupported_doNotRaiseError(
    mocker, db_engine_path
):
    """Test Vulnerability Model implementation."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    create_scan_db = models.Scan.create("test")
    models.Vulnerability.create(
        title="MyVuln",
        short_description="Xss",
        description="Javascript Vuln",
        recommendation="Sanitize data",
        technical_detail="a=$input",
        risk_rating="HIGH",
        cvss_v3_vector="5:6:7",
        dna="121312",
        location={
            "link": {"url": "http://test.com"},
            "metadata": [{"type": "CODE_LOCATION", "value": "some/file.swift:42"}],
        },
        scan_id=create_scan_db.id,
    )

    with models.Database() as session:
        assert session.query(models.Vulnerability).all()[0].location == (
            "Asset: `{\n"
            '    "link": {\n'
            '        "url": "http://test.com"\n'
            "    },\n"
            '    "metadata": [\n'
            "        {\n"
            '            "type": "CODE_LOCATION",\n'
            '            "value": "some/file.swift:42"\n'
            "        }\n"
            "    ]\n"
            "}`\n"
            "CODE_LOCATION: some/file.swift:42  \n"
        )


def testModelsScanStatus_whenDatabaseDoesNotExist_DatabaseAndScanCreated(
    mocker, db_engine_path
):
    """Test Scan Status Model implementation."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    create_scan_db = models.Scan.create("test")

    with models.Database() as session:
        init_count = session.query(models.ScanStatus).count()
    models.ScanStatus.create(
        key="status", value="in_progress", scan_id=create_scan_db.id
    )

    with models.Database() as session:
        assert session.query(models.ScanStatus).count() == init_count + 1
        assert session.query(models.ScanStatus).all()[-1].key == "status"
        assert session.query(models.ScanStatus).all()[-1].value == "in_progress"
        assert session.query(models.ScanStatus).all()[-1].scan_id == create_scan_db.id


def testModelsVulnerability_whenRiskRatingIsCritcal_doNotRaiseError(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Test Vulnerability Model implementation when the risk rating is `Critical`."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    create_scan_db = models.Scan.create("test")
    models.Vulnerability.create(
        title="Critical Vuln",
        short_description="XSS",
        description="Javascript Critical vuln",
        recommendation="Sanitize data",
        technical_detail="a=$input",
        risk_rating="CRITICAL",
        cvss_v3_vector="5:6:7",
        dna="121312",
        location={
            "link": {"url": "http://test.com"},
            "metadata": [{"type": "CODE_LOCATION", "value": "some/file.swift:42"}],
        },
        scan_id=create_scan_db.id,
    )

    with models.Database() as session:
        assert session.query(models.Vulnerability).first().title == "Critical Vuln"
        assert (
            session.query(models.Vulnerability).first().risk_rating
            == risk_rating.RiskRating.CRITICAL
        )
        assert (
            session.query(models.Vulnerability).first().description
            == "Javascript Critical vuln"
        )
        assert session.query(models.Vulnerability).first().scan_id == create_scan_db.id


def testModelsAgent_always_createsAgent(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Test Agent save implementation."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    models.Agent.create("test")

    with models.Database() as session:
        assert session.query(models.Agent).count() == 1
        assert session.query(models.Agent).all()[0].key == "test"


def testModelsAgentArgument_always_createsAgentArgument(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Test Agent Argument save implementation."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    create_agent_db = models.Agent.create("test")
    models.AgentArgument.create(
        agent_id=create_agent_db.id,
        name="test",
        type="test",
        description="test",
        value="test",
    )

    with models.Database() as session:
        assert session.query(models.AgentArgument).count() == 1
        assert session.query(models.AgentArgument).all()[0].name == "test"
        assert session.query(models.AgentArgument).all()[0].type == "test"
        assert session.query(models.AgentArgument).all()[0].description == "test"
        assert session.query(models.AgentArgument).all()[0].value == "test"
        assert (
            session.query(models.AgentArgument).all()[0].agent_id == create_agent_db.id
        )


def testModelsAgentGroup_always_createsAgentGroup(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Test Agent Group save implementation."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    models.AgentGroup.create("test", "test")

    with models.Database() as session:
        assert session.query(models.AgentGroup).count() == 1
        assert session.query(models.AgentGroup).all()[0].name == "test"
        assert session.query(models.AgentGroup).all()[0].description == "test"


def testModelsAgentGroupMapping_always_createsAgentGroupMapping(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Test Agent Group Mapping save implementation."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    agent = models.Agent.create("test")
    agent_group = models.AgentGroup.create("test", "test")
    models.AgentGroupMapping.create(agent_id=agent.id, agent_group_id=agent_group.id)

    with models.Database() as session:
        assert session.query(models.Agent).count() == 1
        assert session.query(models.AgentGroup).count() == 1
        assert session.query(models.AgentGroupMapping).count() == 1
        assert (
            session.query(models.Agent).all()[0].agent_groups[0].name
            == agent_group.name
        )
        assert session.query(models.AgentGroup).all()[0].agents[0].key == agent.key
