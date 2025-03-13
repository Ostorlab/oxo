"""Tests for Models class."""

from pytest_mock import plugin

from ostorlab.runtimes.local.models import models
from ostorlab.utils import risk_rating
from ostorlab.assets import ios_ipa
from ostorlab.assets import android_aab
from ostorlab.assets import android_apk


def testModels_whenDatabaseDoesNotExist_DatabaseAndScanCreated(mocker, db_engine_path):
    """Test when database does not exists, scan is populated in a newly created database."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    models.Scan.create(title="test")

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


def testAssetModels_whenCreateNetwork_assetCreated(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Ensure we correctly persist the network information."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    models.Network.create(
        networks=[
            {"host": "8.8.8.8", "mask": "24"},
            {"host": "42.42.42.42", "mask": "32"},
        ]
    )

    with models.Database() as session:
        assert session.query(models.Network).count() == 1
        network_id = session.query(models.Network).all()[0].id
        ips = (
            session.query(models.IPRange)
            .filter(models.IPRange.network_asset_id == network_id)
            .all()
        )
        assert len(ips) == 2
        assert ips[0].host == "8.8.8.8"
        assert ips[0].mask == "24"
        assert ips[1].host == "42.42.42.42"
        assert ips[1].mask == "32"


def testAssetModels_whenCreateDomainAsset_assetCreated(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Ensure we correctly persist the domain information."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    models.DomainAsset.create(
        domains=[{"name": "domain1.test.ma"}, {"name": "domain2.test.ma"}]
    )

    with models.Database() as session:
        assert session.query(models.DomainAsset).count() == 1
        domain_id = session.query(models.DomainAsset).all()[0].id
        domain_names = (
            session.query(models.DomainName)
            .filter(models.DomainName.domain_asset_id == domain_id)
            .all()
        )
        assert len(domain_names) == 2
        assert domain_names[0].name == "domain1.test.ma"
        assert domain_names[1].name == "domain2.test.ma"


def testAssetModels_whenCreateUrl_assetCreated(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Ensure we correctly persist the list of target URLs information."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    models.Urls.create(
        links=[
            {"url": "https://example24.com", "method": "POST"},
            {"url": "https://example42.com"},
        ]
    )

    with models.Database() as session:
        assert session.query(models.Urls).count() == 1
        url_id = session.query(models.Urls).all()[0].id
        links = (
            session.query(models.Link).filter(models.Link.urls_asset_id == url_id).all()
        )
        assert len(links) == 2
        assert links[0].url == "https://example24.com"
        assert links[0].method == "POST"
        assert links[1].url == "https://example42.com"
        assert links[1].method == "GET"


def testNetworkModel_whenDeleteNetwork_networkDeletedWithItsIps(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Ensure we correctly delete the network and its IPs."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    network = models.Network.create(
        networks=[{"host": "8.8.8.8", "mask": 24}, {"host": "42.42.42.42", "mask": 32}]
    )
    network_id = network.id

    models.Network.delete(network_id)

    with models.Database() as session:
        assert session.query(models.Network).filter_by(id=network_id).count() == 0
        assert (
            session.query(models.IPRange).filter_by(network_asset_id=network_id).count()
            == 0
        )


def testUrlModel_whenDeleteUrl_urlDeletedWithItsLinks(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Ensure we correctly delete the url and its links."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    url = models.Urls.create(
        links=[
            {"url": "https://example24.com", "method": "POST"},
            {"url": "https://example42.com"},
        ]
    )
    url_id = url.id

    models.Urls.delete(url_id)

    with models.Database() as session:
        assert session.query(models.Urls).filter_by(id=url_id).count() == 0
        assert session.query(models.Link).filter_by(urls_asset_id=url_id).count() == 0


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
    scan = models.Scan.create(title="Scan 42")
    with models.Database() as session:
        asset = models.AndroidStore(
            package_name="a.b.c", application_name="Dummy application", scan_id=scan.id
        )
        session.add(asset)
        session.commit()

    with models.Database() as session:
        assert session.query(models.Scan).count() == 1
        scan = session.query(models.Scan).all()[0]
        assert scan.title == "Scan 42"
        assert scan.progress.name == "NOT_STARTED"
        scan_asset = (
            session.query(models.AndroidStore).filter_by(scan_id=scan.id).first()
        )
        assert scan_asset.package_name == "a.b.c"
        assert scan_asset.application_name == "Dummy application"


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


def testCreateAgentGroupWithAssetTypes_always_createsAgentGroupWithAssetTypes(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Test creating an AgentGroup with associated AssetTypes."""

    mocker.patch.object(models, "ENGINE_URL", db_engine_path)

    with models.Database() as session:
        models.AgentGroup.create(
            name="Test Group",
            description="Test Description",
            asset_types=[
                models.AssetTypeEnum.IP,
                models.AssetTypeEnum.DOMAIN,
                models.AssetTypeEnum.LINK,
            ],
            agents=[],
        )

        db_agent_group = (
            session.query(models.AgentGroup).filter_by(name="Test Group").first()
        )
        assert db_agent_group is not None
        assert len(db_agent_group.asset_types) == 3
        assert models.AssetTypeEnum.IP in [
            asset_type.type for asset_type in db_agent_group.asset_types
        ]
        assert models.AssetTypeEnum.DOMAIN in [
            asset_type.type for asset_type in db_agent_group.asset_types
        ]
        assert models.AssetTypeEnum.LINK in [
            asset_type.type for asset_type in db_agent_group.asset_types
        ]


def testGetAgentGroupsByAssetType_always_retrievesAgentGroupsByAssetType(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Test retrieving AgentGroups based on AssetType."""

    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    with models.Database() as session:
        agent_group_1 = models.AgentGroup.create(
            name="Group 1",
            description="Group 1 Description",
            agents=[],
            asset_types=[models.AssetTypeEnum.IP, models.AssetTypeEnum.LINK],
        )
        agent_group_2 = models.AgentGroup.create(
            name="Group 2",
            description="Group 2 Description",
            agents=[],
            asset_types=[models.AssetTypeEnum.LINK],
        )

        agent_groups_ip = (
            session.query(models.AgentGroup)
            .join(models.AgentGroup.asset_types)
            .filter_by(type=models.AssetTypeEnum.IP)
            .all()
        )
        agent_groups_link = (
            session.query(models.AgentGroup)
            .join(models.AgentGroup.asset_types)
            .filter_by(type=models.AssetTypeEnum.LINK)
            .all()
        )

        assert len(agent_groups_ip) == 1
        assert agent_group_1.name in [group.name for group in agent_groups_ip]
        assert agent_group_1.description in [
            group.description for group in agent_groups_ip
        ]
        assert len(agent_groups_link) == 2
        assert agent_group_1.name in [group.name for group in agent_groups_link]
        assert agent_group_2.name in [group.name for group in agent_groups_link]
        assert agent_group_1.description in [
            group.description for group in agent_groups_link
        ]
        assert agent_group_2.description in [
            group.description for group in agent_groups_link
        ]


def testWhenNewVulnerabilityReported_always_scanRiskRatingIsUpdated(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Test updating the scan risk rating when a new vulnerability is reported."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    scan = models.Scan.create(title="Test Scan")

    models.Vulnerability.create(
        title="Info Vuln",
        short_description="Info",
        description="Informational vuln",
        recommendation="None",
        technical_detail="None",
        risk_rating="INFO",
        cvss_v3_vector="0:0:0",
        dna="121312",
        location={},
        scan_id=scan.id,
        references=[],
    )

    with models.Database() as session:
        assert session.query(models.Scan).count() == 1
        scan = session.query(models.Scan).all()[0]
        assert scan.risk_rating == risk_rating.RiskRating.INFO
        scan_vulnz = (
            session.query(models.Vulnerability).filter_by(scan_id=scan.id).all()
        )
        assert len(scan_vulnz) == 1
        assert scan_vulnz[0].risk_rating == risk_rating.RiskRating.INFO

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
        scan_id=scan.id,
        references=[
            {
                "title": "C++ Core Guidelines R.10 - Avoid malloc() and free()",
                "url": "url",
            }
        ],
    )

    with models.Database() as session:
        assert session.query(models.Scan).count() == 1
        scan = session.query(models.Scan).all()[0]
        assert scan.risk_rating == risk_rating.RiskRating.CRITICAL
        scan_vulnz = (
            session.query(models.Vulnerability).filter_by(scan_id=scan.id).all()
        )
        assert len(scan_vulnz) == 2
        assert any(
            vuln.risk_rating == risk_rating.RiskRating.CRITICAL for vuln in scan_vulnz
        )
        assert any(
            vuln.risk_rating == risk_rating.RiskRating.INFO for vuln in scan_vulnz
        )


def testAssetModels_whenCreateFromAssetsDefinitionWithIOSIpaPath_iOSFileCreated(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Ensure iOS IPA file asset is correctly created from path."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    mocker.patch.object(models.utils, "get_bundle_id", return_value="test.bundle.id")
    ios_ipa_asset = ios_ipa.IOSIpa(path="/path/to/app.ipa")

    models.Asset.create_from_assets_definition([ios_ipa_asset])

    with models.Database() as session:
        assets = session.query(models.IosFile).all()
        assert len(assets) == 1
        assert assets[0].path == "/path/to/app.ipa"
        assert assets[0].bundle_id == "test.bundle.id"


def testAssetModels_whenCreateFromAssetsDefinitionWithIOSIpaUrl_iOSFileCreated(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Ensure iOS IPA file asset is correctly created from URL."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    ios_ipa_asset = ios_ipa.IOSIpa(content_url="https://example.com/app.ipa")

    models.Asset.create_from_assets_definition([ios_ipa_asset])

    with models.Database() as session:
        assets = session.query(models.IosFile).all()
        assert len(assets) == 1
        assert assets[0].path == "https://example.com/app.ipa"
        assert assets[0].bundle_id == "N/A"


def testAssetModels_whenCreateFromAssetsDefinitionWithAndroidApkPath_androidFileCreated(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Ensure Android APK file asset is correctly created from path."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    mocker.patch.object(models.utils, "get_package_name", return_value="com.test.app")
    apk_asset = android_apk.AndroidApk(path="/path/to/app.apk")

    models.Asset.create_from_assets_definition([apk_asset])

    with models.Database() as session:
        assets = session.query(models.AndroidFile).all()
        assert len(assets) == 1
        assert assets[0].path == "/path/to/app.apk"
        assert assets[0].package_name == "com.test.app"


def testAssetModels_whenCreateFromAssetsDefinitionWithAndroidApkUrl_androidFileCreated(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Ensure Android APK file asset is correctly created from URL."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    apk_asset = android_apk.AndroidApk(content_url="https://example.com/app.apk")

    models.Asset.create_from_assets_definition([apk_asset])

    with models.Database() as session:
        assets = session.query(models.AndroidFile).all()
        assert len(assets) == 1
        assert assets[0].path == "https://example.com/app.apk"
        assert assets[0].package_name == "N/A"


def testAssetModels_whenCreateFromAssetsDefinitionWithAndroidAabPath_androidFileCreated(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Ensure Android AAB file asset is correctly created from path."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    mocker.patch.object(models.utils, "get_package_name", return_value="com.test.aab")
    aab_asset = android_aab.AndroidAab(path="/path/to/app.aab")

    models.Asset.create_from_assets_definition([aab_asset])

    with models.Database() as session:
        assets = session.query(models.AndroidFile).all()
        assert len(assets) == 1
        assert assets[0].path == "/path/to/app.aab"
        assert assets[0].package_name == "com.test.aab"


def testAssetModels_whenCreateFromAssetsDefinitionWithAndroidAabUrl_androidFileCreated(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Ensure Android AAB file asset is correctly created from URL."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    aab_asset = android_aab.AndroidAab(content_url="https://example.com/app.aab")

    models.Asset.create_from_assets_definition([aab_asset])

    with models.Database() as session:
        assets = session.query(models.AndroidFile).all()
        assert len(assets) == 1
        assert assets[0].path == "https://example.com/app.aab"
        assert assets[0].package_name == "N/A"
