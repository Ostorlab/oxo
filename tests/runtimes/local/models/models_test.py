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


# class Agent(Base):
#     """The Agent model"""
#
#     __tablename__ = "agent"
#     id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
#     key = sqlalchemy.Column(sqlalchemy.String(255))
#
#     agent_groups = orm.relationship(
#         "AgentGroup", secondary="agent_group_mapping", back_populates="agents"
#     )
#
#     @staticmethod
#     def create(key: str) -> "Agent":
#         """Persist the agent in the database.
#
#         Args:
#             key: Agent key.
#         Returns:
#             Agent object.
#         """
#         agent = Agent(key=key)
#         with Database() as session:
#             session.add(agent)
#             session.commit()
#             return agent
#
#
# class AgentArgument(Base):
#     """The Agent Argument model"""
#
#     __tablename__ = "agent_argument"
#     id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
#     name = sqlalchemy.Column(sqlalchemy.String(255))
#     type = sqlalchemy.Column(sqlalchemy.String(255))
#     description = sqlalchemy.Column(sqlalchemy.Text)
#     default_value = sqlalchemy.Column(sqlalchemy.Text)
#
#     agent_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("agent.id"))
#
#     @staticmethod
#     def create(
#         agent_id: int,
#         name: str,
#         type: str,
#         description: Optional[str] = None,
#         default_value: Optional[str] = None,
#     ) -> "AgentArgument":
#         """Persist the agent argument in the database.
#
#         Args:
#             agent_id: Agent id.
#             name: Argument name.
#             type: Argument type.
#             description: Argument description.
#             default_value: Argument default value.
#         Returns:
#             AgentArgument object.
#         """
#         agent_argument = AgentArgument(
#             agent_id=agent_id,
#             name=name,
#             type=type,
#             description=description,
#             default_value=default_value,
#         )
#         with Database() as session:
#             session.add(agent_argument)
#             session.commit()
#             return agent_argument
#
#
# class AgentGroup(Base):
#     """The Agent Group model"""
#
#     __tablename__ = "agent_group"
#     id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
#     key = sqlalchemy.Column(sqlalchemy.String(255))
#     description = sqlalchemy.Column(sqlalchemy.Text)
#     asset_type = sqlalchemy.Column(sqlalchemy.Enum(AssetType))
#     created_time = sqlalchemy.Column(sqlalchemy.DateTime)
#
#     agents = orm.relationship(
#         "Agent", secondary="agent_group_mapping", back_populates="agent_groups"
#     )
#
#     @staticmethod
#     def create(key: str, description: str, asset_type: AssetType) -> "AgentGroup":
#         """Persist the agent group in the database.
#
#         Args:
#             key: Agent group key.
#             description: Agent group description.
#             asset_type: Asset type, which is the type of the asset the agent group is targeting.
#         Returns:
#             AgentGroup object.
#         """
#         agent_group = AgentGroup(
#             key=key,
#             description=description,
#             asset_type=asset_type,
#             created_time=datetime.datetime.now(),
#         )
#         with Database() as session:
#             session.add(agent_group)
#             session.commit()
#             return agent_group
#
#
# class AgentGroupMapping(Base):
#     """The Agent Group Mapping model"""
#
#     __tablename__ = "agent_group_mapping"
#     agent_id = sqlalchemy.Column(
#         sqlalchemy.Integer, sqlalchemy.ForeignKey("agent.id"), primary_key=True
#     )
#     agent_group_id = sqlalchemy.Column(
#         sqlalchemy.Integer, sqlalchemy.ForeignKey("agent_group.id"), primary_key=True
#     )


def testModelsAgent_always_createsAgent(mocker, db_engine_path):
    """Test Agent save implementation."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    models.Agent.create("test")

    with models.Database() as session:
        assert session.query(models.Agent).count() == 1
        assert session.query(models.Agent).all()[0].key == "test"


def testModelsAgentArgument_always_createsAgentArgument(mocker, db_engine_path):
    """Test Agent Argument save implementation."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    create_agent_db = models.Agent.create("test")
    models.AgentArgument.create(
        agent_id=create_agent_db.id,
        name="test",
        type="test",
        description="test",
        default_value="test",
    )

    with models.Database() as session:
        assert session.query(models.AgentArgument).count() == 1
        assert session.query(models.AgentArgument).all()[0].name == "test"
        assert session.query(models.AgentArgument).all()[0].type == "test"
        assert session.query(models.AgentArgument).all()[0].description == "test"
        assert session.query(models.AgentArgument).all()[0].default_value == "test"
        assert session.query(models.AgentArgument).all()[0].agent_id == create_agent_db.id


def testModelsAgentGroup_always_createsAgentGroup(mocker, db_engine_path):
    """Test Agent Group save implementation."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    models.AgentGroup.create("test", "test", {"asset_types": ["type1","type2"]})

    with models.Database() as session:
        assert session.query(models.AgentGroup).count() == 1
        assert session.query(models.AgentGroup).all()[0].key == "test"
        assert session.query(models.AgentGroup).all()[0].description == "test"
        assert session.query(models.AgentGroup).all()[0].asset_types == {'asset_types': ['type1', 'type2']}


def testModelsAgentGroupMapping_always_createsAgentGroupMapping(mocker, db_engine_path):
    """Test Agent Group Mapping save implementation."""
    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    agent = models.Agent.create("test")
    agent_group = models.AgentGroup.create("test", "test", {"asset_types": ["type1","type2"]})
    models.AgentGroupMapping.create(agent_id=agent.id, agent_group_id=agent_group.id)

    with models.Database() as session:
        assert session.query(models.Agent).count() == 1
        assert session.query(models.AgentGroup).count() == 1
        assert session.query(models.AgentGroupMapping).count() == 1
        assert session.query(models.Agent).all()[0].agent_groups[0].key == agent_group.key
        assert session.query(models.Agent).all()[0].agent_groups[0].asset_types == agent_group.asset_types
        assert session.query(models.AgentGroup).all()[0].agents[0].key == agent.key


