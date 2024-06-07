"""models contain the database engine logic and all the db models and the related operations."""

import datetime
import enum
import json
import logging
import pathlib
import uuid
import types
from typing import Any, Dict, List, Optional

import sqlalchemy
from sqlalchemy import orm
from sqlalchemy.ext import declarative
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.engine import base
from alembic import config
from alembic import script
from alembic import command as alembic_command
from alembic.runtime import migration
from alembic.util import exc as alembic_exceptions

from ostorlab import configuration_manager as config_manager
from ostorlab.cli import console as cli_console
from ostorlab.utils import risk_rating as utils_rik_rating

ENGINE_URL = f"sqlite:///{config_manager.ConfigurationManager().conf_path}/db.sqlite"
OSTORLAB_BASE_MIGRATION_ID = "35cd577ef0e5"

logger = logging.getLogger(__name__)
console = cli_console.Console()

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = sqlalchemy.MetaData(naming_convention=convention)
Base = declarative.declarative_base(metadata=metadata)


class ScanProgress(enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    STOPPED = "stopped"
    DONE = "done"
    ERROR = "error"


class Database:
    """Handles all Database instantiation and calls."""

    def __init__(self):
        """Constructs the database engine."""
        self._db_engine = sqlalchemy.create_engine(
            ENGINE_URL, connect_args={"check_same_thread": False}
        )
        self._db_session = None
        self._alembic_ini_path = (
            pathlib.Path(__file__).parent.absolute() / "alembic.ini"
        )
        self._alembic_cfg = config.Config(str(self._alembic_ini_path))

    def __enter__(self) -> orm.Session:
        """Context manager enter method, resposible for migrating the local database and returning a session object."""
        self._migrate_local_db()
        return self._prepare_db_session()

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_traceback: Optional[types.TracebackType],
    ) -> None:
        """Context manager exit method, responsible for closing the local database session"""
        if self._db_session is not None:
            self._db_session.close()

    def _is_db_populated(self, conn: base.Connection) -> bool:
        """Checks if the local database has tables."""
        inspector = Inspector.from_engine(conn)
        tables = inspector.get_table_names()
        return len(tables) != 0

    def _migrate_local_db(self) -> None:
        """Ensure the local database schema is up to date & run the migration otherwise."""
        try:
            alembic_script = script.ScriptDirectory.from_config(self._alembic_cfg)
            with self._db_engine.begin() as conn:
                context = migration.MigrationContext.configure(conn)
                # To ensure backward  compatibility with existing databases,
                # the next two lines do a fake migration of the base schema,
                # before applying the migrations from that point.
                if (
                    self._is_db_populated(conn)
                    and context.get_current_revision() is None
                ):
                    alembic_command.stamp(self._alembic_cfg, OSTORLAB_BASE_MIGRATION_ID)

                if context.get_current_revision() != alembic_script.get_current_head():
                    alembic_command.upgrade(self._alembic_cfg, "head")
        except (alembic_exceptions.CommandError, ValueError) as e:
            console.error(f"Error while migrating the local database: {str(e)}")

    def _prepare_db_session(self) -> orm.Session:
        """Returns a Session singleton to run queries on the db engine."""
        if self._db_session is None:
            session_maker = orm.sessionmaker(expire_on_commit=False)
            session_maker.configure(bind=self._db_engine)
            self._db_session = session_maker()
            return self._db_session
        else:
            return self._db_session

    def create_db_tables(self):
        """Create the database tables."""
        with self._db_engine.begin() as conn:
            metadata.create_all(conn)
            logger.info("Tables created")

    def drop_db_tables(self):
        """Drop the database tables."""
        metadata.drop_all(self._db_engine)
        logger.info("Tables dropped")


class Scan(Base):
    """The Scan model"""

    __tablename__ = "scan"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    title = sqlalchemy.Column(sqlalchemy.String(255))
    asset = sqlalchemy.Column(sqlalchemy.String(255))
    created_time = sqlalchemy.Column(sqlalchemy.DateTime)
    progress = sqlalchemy.Column(sqlalchemy.Enum(ScanProgress))
    agent_group_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("agent_group.id")
    )

    @staticmethod
    def create(
        asset: str,
        title: str = "",
        agent_group_id: Optional[int] = None,
        progress: sqlalchemy.Enum(ScanProgress) = ScanProgress.NOT_STARTED,
    ) -> "Scan":
        """Persist the scan in the database.

        Args:
            asset: Asset to scan.
            title: Scan title.
            progress: Scan progress.
        Returns:
            Scan object.
        """
        with Database() as session:
            scan = Scan(
                title=title,
                asset=asset,
                created_time=datetime.datetime.now(),
                progress=progress,
                agent_group_id=agent_group_id,
            )
            session.add(scan)
            session.commit()
            return scan


class Vulnerability(Base):
    """The Vulnerability model"""

    __tablename__ = "vulnerability"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    technical_detail = sqlalchemy.Column(sqlalchemy.Text)
    risk_rating = sqlalchemy.Column(sqlalchemy.Enum(utils_rik_rating.RiskRating))
    cvss_v3_vector = sqlalchemy.Column(sqlalchemy.String(1024))
    dna = sqlalchemy.Column(sqlalchemy.String(256))
    title = sqlalchemy.Column(sqlalchemy.String(256))
    short_description = sqlalchemy.Column(sqlalchemy.Text)
    description = sqlalchemy.Column(sqlalchemy.Text)
    recommendation = sqlalchemy.Column(sqlalchemy.Text)
    references = sqlalchemy.Column(sqlalchemy.Text)
    scan_id = sqlalchemy.Column(
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey("scan.id"),
    )
    location = sqlalchemy.Column(sqlalchemy.Text)

    @staticmethod
    def _prepare_references_markdown(references: List[Dict[str, str]]) -> str:
        """Returns a markdown display of the references of a vulnerability."""
        if references is None or len(references) == 0:
            return ""
        references_markdwon_value = ""

        for reference in references:
            title = reference.get("title", "")
            url = reference.get("url", "")
            reference_markdwon = f"{title}: {url}  \n"
            references_markdwon_value += reference_markdwon

        return references_markdwon_value

    @staticmethod
    def _prepare_vuln_location_markdown(location: Dict[str, Any]) -> str:
        """Returns a markdown display of the exact target where the vulnerability was found."""
        if location is None:
            return ""
        location_markdwon_value = ""
        if location.get("domain_name") is not None:
            domain_name = location["domain_name"].get("name")
            location_markdwon_value = f"Domain: `{domain_name}`\n"
        elif location.get("ipv4") is not None:
            host = location["ipv4"].get("host")
            location_markdwon_value = f"IPv4: `{host}`\n"
        elif location.get("ipv6") is not None:
            host = location["ipv6"].get("host")
            location_markdwon_value = f"IPv6: `{host}`\n"
        elif location.get("android_store") is not None:
            package_name = location["android_store"].get("package_name")
            location_markdwon_value = f"Android: `{package_name}`\n"
        elif location.get("ios_store") is not None:
            bundle_id = location["ios_store"].get("bundle_id")
            location_markdwon_value = f"iOS: `{bundle_id}`\n"
        else:
            location_markdwon_value = f"Asset: `{json.dumps(location, indent=4)}`\n"

        for metadata_dict in location.get("metadata", []):
            metad_type = metadata_dict.get("type")
            metad_value = metadata_dict.get("value")
            location_markdwon_value += f"{metad_type}: {metad_value}  \n"
        return location_markdwon_value

    @staticmethod
    def create(
        scan_id: int,
        title: str,
        short_description: str,
        description: str,
        recommendation: str,
        technical_detail: str,
        risk_rating: str,
        cvss_v3_vector: Optional[str] = None,
        dna: Optional[str] = None,
        references: Optional[List[Dict[str, str]]] = None,
        location: Optional[Dict[str, Any]] = None,
    ):
        """Persist the vulnerability in the database.

        Args:
            scan_id: Scan id of the vulnerability.
            title: Vulnerability title.
            false_positive: Boolean to True if the vulnerability is a false positive.
            dna: A unique string to determine a vulnerability and avoid duplicates in the database.
            cvss_v3_vector: Common vulnerability scoring system value.
            risk_rating: Vulnerability risk rating.
            technical_detail: Technical details to demonstrate the finding.
            description: A generic description of the vulnerability.
            short_description: A short description of the vulnerability.
            recommendation: How to address or avoid the vulnerability
            references: List of references for extra information about the vulnerability.
            location: In which exact target the vulnerability was found.
        Returns:
            Vulnerability object.
        """
        references_md = Vulnerability._prepare_references_markdown(references)
        vuln_location = Vulnerability._prepare_vuln_location_markdown(location)
        vuln = Vulnerability(
            scan_id=scan_id,
            title=title,
            short_description=short_description,
            description=description,
            recommendation=recommendation,
            references=references_md,
            technical_detail=technical_detail,
            risk_rating=risk_rating,
            cvss_v3_vector=cvss_v3_vector,
            dna=dna,
            location=vuln_location,
        )

        with Database() as session:
            session.add(vuln)
            session.commit()

        for reference in references:
            Reference.create(
                title=reference.get("title", ""),
                url=reference.get("url", ""),
                vulnerability_id=vuln.id,
            )

        return vuln


class ScanStatus(Base):
    """The Scan Status model"""

    __tablename__ = "scan_status"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    created_time = sqlalchemy.Column(sqlalchemy.DateTime)
    key = sqlalchemy.Column(sqlalchemy.String(255))
    value = sqlalchemy.Column(sqlalchemy.Text)
    scan_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("scan.id"))

    @staticmethod
    def create(key: str, value: str, scan_id: int):
        """Persist the scan status in the database.

        Args:
            key: Scan status key.
            value: Scan status value.
        Returns:
            Scan status object.
        """
        scan_status = ScanStatus(
            key=key, created_time=datetime.datetime.now(), value=value, scan_id=scan_id
        )
        with Database() as session:
            session.add(scan_status)
            session.commit()
            return scan_status


class Reference(Base):
    """The Reference model"""

    __tablename__ = "reference"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    title = sqlalchemy.Column(sqlalchemy.String(255))
    url = sqlalchemy.Column(sqlalchemy.String(4096))
    vulnerability_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("vulnerability.id")
    )

    @staticmethod
    def create(title: str, url: str, vulnerability_id: int) -> "Reference":
        """Persist the reference in the database.

        Args:
            title: Reference title.
            url: Reference URL.
            vulnerability_id: Vulnerability id.
        Returns:
            Reference object.
        """
        reference = Reference(title=title, url=url, vulnerability_id=vulnerability_id)
        with Database() as session:
            session.add(reference)
            session.commit()
            return reference


class Agent(Base):
    """The Agent model"""

    __tablename__ = "agent"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    key = sqlalchemy.Column(sqlalchemy.String(255))

    agent_groups = orm.relationship(
        "AgentGroup", secondary="agent_group_mapping", back_populates="agents"
    )

    @staticmethod
    def create(key: str) -> "Agent":
        """Persist the agent in the database.

        Args:
            key: Agent key.
        Returns:
            Agent object.
        """
        agent = Agent(key=key)
        with Database() as session:
            session.add(agent)
            session.commit()
            return agent


class AgentArgument(Base):
    """The Agent Argument model"""

    __tablename__ = "agent_argument"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String(255))
    type = sqlalchemy.Column(sqlalchemy.String(255))
    description = sqlalchemy.Column(sqlalchemy.Text)
    value = sqlalchemy.Column(sqlalchemy.LargeBinary)

    agent_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("agent.id"))

    @staticmethod
    def create(
        agent_id: int,
        name: str,
        type: str,
        description: Optional[str] = None,
        value: Optional[bytes] = None,
    ) -> "AgentArgument":
        """Persist the agent argument in the database.

        Args:
            agent_id: Agent id.
            name: Argument name.
            type: Argument type.
            description: Argument description.
            value: Argument default value.
        Returns:
            AgentArgument object.
        """
        agent_argument = AgentArgument(
            agent_id=agent_id,
            name=name,
            type=type,
            description=description,
            value=value,
        )
        with Database() as session:
            session.add(agent_argument)
            session.commit()
            return agent_argument


class AgentGroup(Base):
    """The Agent Group model"""

    __tablename__ = "agent_group"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String(255))
    description = sqlalchemy.Column(sqlalchemy.Text)
    created_time = sqlalchemy.Column(sqlalchemy.DateTime)

    agents = orm.relationship(
        "Agent", secondary="agent_group_mapping", back_populates="agent_groups"
    )

    @staticmethod
    def create(name: str, description: str, agents: Any) -> "AgentGroup":
        """Persist the agent group in the database.

        Args:
            name: Agent group name.
            description: Agent group description.
            agents: List of agents.
        Returns:
            AgentGroup object.
        """
        agent_group = AgentGroup(
            name=name,
            description=description,
            created_time=datetime.datetime.now(),
        )

        for agent in agents:
            new_agent = Agent.create(agent.key)
            agent_group.agents.append(new_agent)
            for argument in agent.args:
                AgentArgument.create(
                    agent_id=new_agent.id,
                    name=argument.name,
                    type=argument.type,
                    description=argument.description,
                    value=argument.value,
                )

        with Database() as session:
            session.add(agent_group)
            session.commit()
            return agent_group


class AgentGroupMapping(Base):
    """The Agent Group Mapping model"""

    __tablename__ = "agent_group_mapping"
    agent_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("agent.id"), primary_key=True
    )
    agent_group_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("agent_group.id"), primary_key=True
    )

    @staticmethod
    def create(agent_id: int, agent_group_id: int) -> "AgentGroupMapping":
        """Persist the agent group mapping in the database.

        Args:
            agent_id: Agent id.
            agent_group_id: Agent group id.
        Returns:
            AgentGroupMapping object.
        """
        agent_group_mapping = AgentGroupMapping(
            agent_id=agent_id, agent_group_id=agent_group_id
        )
        with Database() as session:
            session.add(agent_group_mapping)
            session.commit()
            return agent_group_mapping


class APIKey(Base):
    """The API Key model"""

    __tablename__ = "api_key"
    key = sqlalchemy.Column(
        sqlalchemy.String(150), unique=True, nullable=False, primary_key=True
    )

    @staticmethod
    def create() -> "APIKey":
        """Persist the API key in the database.

        Returns:
            APIKey object.
        """
        with Database() as session:
            api_key = APIKey(key=str(uuid.uuid4()))
            session.add(api_key)
            session.commit()
            return api_key

    @staticmethod
    def get_or_create() -> "APIKey":
        """Get or create the API key in the database.

        Returns:
            APIKey object.
        """
        with Database() as session:
            api_key = session.query(APIKey).first()
            if api_key is None:
                api_key = APIKey.create()
            return api_key

    @staticmethod
    def is_valid(api_key: str) -> bool:
        """Check if the API key is valid.

        Args:
            api_key: API key to check.
        Returns:
            Boolean.
        """
        with Database() as session:
            api_key = session.query(APIKey).filter_by(key=api_key).first()
            return api_key is not None

    @staticmethod
    def refresh() -> "APIKey":
        """Revoke the current API key and create a new one."""
        with Database() as session:
            session.query(APIKey).delete()
            session.commit()
            api_key = APIKey.create()
            return api_key


class Asset(Base):
    __tablename__ = "asset"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    type = sqlalchemy.Column(sqlalchemy.String(50))
    __mapper_args__ = {
        "polymorphic_identity": "asset",
        "polymorphic_on": type,
    }
    scan_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("scan.id"), nullable=True
    )


class AndroidFile(Asset):
    __tablename__ = "android_file"
    id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("asset.id"), primary_key=True
    )
    package_name = sqlalchemy.Column(sqlalchemy.String(255))
    path = sqlalchemy.Column(sqlalchemy.String(1024))

    __mapper_args__ = {
        "polymorphic_identity": "android_file",
    }

    @staticmethod
    def create(package_name: str = "", path: str = "") -> "AndroidFile":
        """Persist the android file information in the database.

        Args:
            package_name: The application identifier.
            path: Local/Remote path of the APK/AAB.

        Returns:
            android file object.
        """
        with Database() as session:
            asset = AndroidFile(
                package_name=package_name,
                path=path,
            )
            session.add(asset)
            session.commit()
            return asset


class AndroidStore(Asset):
    __tablename__ = "android_store"
    id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("asset.id"), primary_key=True
    )
    package_name = sqlalchemy.Column(sqlalchemy.String(255))
    application_name = sqlalchemy.Column(sqlalchemy.String(255))

    __mapper_args__ = {
        "polymorphic_identity": "android_store",
    }

    @staticmethod
    def create(package_name: str = "", application_name: str = "") -> "AndroidStore":
        """Persist the android store information in the database.

        Args:
            package_name: The application identifier.
            application_name: The application name as shown in the store.

        Returns:
            android store object.
        """
        with Database() as session:
            asset = AndroidStore(
                package_name=package_name,
                application_name=application_name,
            )
            session.add(asset)
            session.commit()
            return asset


class IosFile(Asset):
    __tablename__ = "ios_file"
    id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("asset.id"), primary_key=True
    )
    bundle_id = sqlalchemy.Column(sqlalchemy.String(255))
    path = sqlalchemy.Column(sqlalchemy.String(1024))

    __mapper_args__ = {
        "polymorphic_identity": "ios_file",
    }

    @staticmethod
    def create(bundle_id: str = "", path: str = "") -> "IosFile":
        """Persist the iOS file information in the database.

        Args:
            bundle_id: The application identifier.
            path: Local/Remote path of the IPA.

        Returns:
            iOS file object.
        """
        with Database() as session:
            asset = IosFile(
                bundle_id=bundle_id,
                path=path,
            )
            session.add(asset)
            session.commit()
            return asset


class IosStore(Asset):
    __tablename__ = "ios_store"
    id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("asset.id"), primary_key=True
    )
    bundle_id = sqlalchemy.Column(sqlalchemy.String(255))
    application_name = sqlalchemy.Column(sqlalchemy.String(255))

    __mapper_args__ = {
        "polymorphic_identity": "ios_store",
    }

    @staticmethod
    def create(bundle_id: str = "", application_name: str = "") -> "IosStore":
        """Persist the iOS store information in the database.

        Args:
            bundle_id: The application identifier.
            application_name: The application name as shown in the store.

        Returns:
            iOS store object.
        """
        with Database() as session:
            asset = IosStore(
                bundle_id=bundle_id,
                application_name=application_name,
            )
            session.add(asset)
            session.commit()
            return asset


class Url(Asset):
    __tablename__ = "urls"
    id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("asset.id"), primary_key=True
    )
    links = sqlalchemy.Column(sqlalchemy.String(1024))

    __mapper_args__ = {
        "polymorphic_identity": "urls",
    }

    @staticmethod
    def create(links: List[str]) -> "Url":
        """Persist the URL information in the database.

        Args:
            links: list of the target URLs.

        Returns:
            Url object.
        """
        with Database() as session:
            asset = Url(
                links=json.dumps(links),
            )
            session.add(asset)
            session.commit()
            return asset


class Network(Asset):
    __tablename__ = "network"
    id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("asset.id"), primary_key=True
    )
    networks = sqlalchemy.Column(sqlalchemy.String(1024))

    __mapper_args__ = {
        "polymorphic_identity": "network",
    }

    @staticmethod
    def create(networks: List[str]) -> "Network":
        """Persist the Network information in the database.

        Args:
            networks: list of the target IP/range addresses.

        Returns:
            Network object.
        """
        with Database() as session:
            asset = Network(
                networks=json.dumps(networks),
            )
            session.add(asset)
            session.commit()
            return asset
