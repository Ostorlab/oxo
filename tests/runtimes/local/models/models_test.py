"""Tests for Models class."""

import datetime
import json

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


def testAssetModels_whenCreateNetwork_assetCreated(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Ensure we correctly persist the network information."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    models.Network.create(ips=["8.8.8.8", "42.42.42.42"])

    with models.Database() as session:
        assert session.query(models.Network).count() == 1
        ips = json.loads(session.query(models.Network).all()[0].ips)
        assert ips == ["8.8.8.8", "42.42.42.42"]


def testAssetModels_whenCreateUrl_assetCreated(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Ensure we correctly persist the list of target URLs information."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    models.Url.create(links=["https://example.com", "https://example42.com"])

    with models.Database() as session:
        assert session.query(models.Url).count() == 1
        links = json.loads(session.query(models.Url).all()[0].links)
        assert links == ["https://example.com", "https://example42.com"]


def testAssetModels_whenCreateIosStore_assetCreated(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Ensure we correctly persist the iOS store information."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    models.IosStore.create(bundle_id="a.b.c", application_name="Dummy application")

    with models.Database() as session:
        assert session.query(models.IosStore).count() == 1
        asset = session.query(models.IosStore).all()[0]
        assert asset.bundle_id == "a.b.c"
        assert asset.application_name == "Dummy application"


def testAssetModels_whenCreateAndroidStore_assetCreated(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Ensure we correctly persist the android store information."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    models.AndroidStore.create(
        package_name="a.b.c", application_name="Dummy application"
    )

    with models.Database() as session:
        assert session.query(models.AndroidStore).count() == 1
        asset = session.query(models.AndroidStore).all()[0]
        assert asset.package_name == "a.b.c"
        assert asset.application_name == "Dummy application"


def testAssetModels_whenCreateIosFile_assetCreated(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Ensure we correctly persist the iOS file information."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    models.IosFile.create(bundle_id="a.b.c", path="https://remote.bucket.com/ios_app")

    with models.Database() as session:
        assert session.query(models.IosFile).count() == 1
        asset = session.query(models.IosFile).all()[0]
        assert asset.bundle_id == "a.b.c"
        assert asset.path == "https://remote.bucket.com/ios_app"


def testAssetModels_whenCreateAndroidFile_assetCreated(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Ensure we correctly persist the android file information."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    models.AndroidFile.create(
        package_name="a.b.c", path="https://remote.bucket.com/android_app"
    )

    with models.Database() as session:
        assert session.query(models.AndroidFile).count() == 1
        asset = session.query(models.AndroidFile).all()[0]
        assert asset.package_name == "a.b.c"
        assert asset.path == "https://remote.bucket.com/android_app"


def testAssetModels_whenCreateScan_scanCreatedAndQueryInformation(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Ensure we correctly persist the scan and its asset & query the asset information."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    asset = models.AndroidStore.create(
        package_name="a.b.c", application_name="Dummy application"
    )
    with models.Database() as session:
        scan = models.Scan(
            title="Scan 42",
            asset="a.b.c",
            created_time=datetime.datetime.now(),
            progress="NOT_STARTED",
            asset_id=asset.id,
            asset_instance=asset,
        )
        session.add(scan)
        session.commit()

    with models.Database() as session:
        assert session.query(models.Scan).count() == 1
        scan = session.query(models.Scan).all()[0]
        assert scan.title == "Scan 42"
        assert scan.progress.name == "NOT_STARTED"
        asset_instance = scan.asset_instance
        assert asset_instance.type == "android_store"
        assert asset_instance.package_name == "a.b.c"
        assert asset_instance.application_name == "Dummy application"
        assert len(session.query(models.AndroidStore).all()[0].scans) == 1


def testAssetModels_whenMultipleAssets_shouldHaveUniqueIdsPerTable(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Ensure we correctly assets depending on their type and their IDs are unique in the base asset table."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    models.AndroidStore.create(
        package_name="a.b.c", application_name="Dummy application"
    )
    models.IosStore.create(bundle_id="a.b.c", application_name="Dummy application")

    with models.Database() as session:
        assert session.query(models.Asset).count() == 2
        assert session.query(models.AndroidStore).count() == 1
        assert session.query(models.IosStore).count() == 1
        assert (
            session.query(models.Asset).all()[0].id
            == session.query(models.AndroidStore).all()[0].id
        )
        assert (
            session.query(models.Asset).all()[1].id
            == session.query(models.IosStore).all()[0].id
        )
