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
        references=[],
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
        references=[],
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
        references=[
            {
                "title": "C++ Core Guidelines R.10 - Avoid malloc() and free()",
                "url": "https://github.com/isocpp/CppCoreGuidelines/blob/036324/CppCoreGuidelines.md#r10-avoid-malloc-and-free",
            }
        ],
    )

    with models.Database() as session:
        vuln = session.query(models.Vulnerability).first()
        assert vuln.title == "Critical Vuln"
        assert vuln.risk_rating == risk_rating.RiskRating.CRITICAL
        assert vuln.description == "Javascript Critical vuln"
        assert vuln.scan_id == create_scan_db.id
        references = (
            session.query(models.Reference)
            .filter(models.Reference.vulnerability_id == vuln.id)
            .all()
        )
        assert len(references) == 1
        assert (
            references[0].title
            == "C++ Core Guidelines R.10 - Avoid malloc() and free()"
        )
        assert (
            references[0].url
            == "https://github.com/isocpp/CppCoreGuidelines/blob/036324/CppCoreGuidelines.md#r10-avoid-malloc-and-free"
        )


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
        value=b"test",
    )

    with models.Database() as session:
        assert session.query(models.AgentArgument).count() == 1
        assert session.query(models.AgentArgument).all()[0].name == "test"
        assert session.query(models.AgentArgument).all()[0].type == "test"
        assert session.query(models.AgentArgument).all()[0].description == "test"
        assert session.query(models.AgentArgument).all()[0].value == b"test"
        assert (
            session.query(models.AgentArgument).all()[0].agent_id == create_agent_db.id
        )


def testModelsAgentGroup_always_createsAgentGroup(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Test Agent Group save implementation."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)

    with models.Database() as session:
        ag = models.AgentGroup(name="test", description="test")
        session.add(ag)
        session.commit()

        assert session.query(models.AgentGroup).count() == 1
        assert session.query(models.AgentGroup).all()[0].name == "test"
        assert session.query(models.AgentGroup).all()[0].description == "test"


def testModelsAgentGroupMapping_always_createsAgentGroupMapping(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Test Agent Group Mapping save implementation."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)

    with models.Database() as session:
        agent = models.Agent(key="test")
        session.add(agent)
        session.commit()
        agent_group = models.AgentGroup(name="test", description="test")
        session.add(agent_group)
        session.commit()
        models.AgentGroupMapping.create(
            agent_id=agent.id, agent_group_id=agent_group.id
        )

        assert session.query(models.Agent).count() == 1
        assert session.query(models.AgentGroup).count() == 1
        assert session.query(models.AgentGroupMapping).count() == 1
        assert (
            session.query(models.Agent).all()[0].agent_groups[0].name
            == agent_group.name
        )
        assert session.query(models.AgentGroup).all()[0].agents[0].key == agent.key


def testModelsAPIKeyGetOrCreate_never_createsNewAPIKeyIfOneExists(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Test API Key get_or_create implementation."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)

    models.APIKey.get_or_create()
    models.APIKey.get_or_create()
    with models.Database() as session:
        assert session.query(models.APIKey).count() == 1


def testModelsAPIKeyValidation_whenKeyIsValid_returnsTrue(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Test API Key validation implementation."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)

    api_key = models.APIKey.get_or_create()

    assert api_key.is_valid(api_key.key) is True


def testModelsAPIKeyValidation_whenKeyIsInvalid_returnsFalse(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Test API Key validation implementation."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)

    api_key = models.APIKey.get_or_create()

    assert api_key.is_valid("invalid_key") is False


def testModelsAPIKeyRefresh_always_createsNewAPIKey(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Test API Key refresh implementation."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    current_api_key = models.APIKey.get_or_create()

    models.APIKey.refresh()

    new_api_key = models.APIKey.get_or_create()
    assert current_api_key.key != new_api_key.key
