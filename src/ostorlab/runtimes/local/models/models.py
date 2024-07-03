"""models contain the database engine logic and all the db models and the related operations."""

import datetime
import enum
import json
import logging
import pathlib
import struct
import uuid
import types
from typing import Any, Dict, List, Optional, Union
import ipaddress

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
from ostorlab.runtimes import definitions
from ostorlab.runtimes.local.models import utils
from ostorlab.utils import risk_rating as utils_rik_rating
from ostorlab.assets import ipv4
from ostorlab.assets import ipv6
from ostorlab.assets import link
from ostorlab.assets import ios_ipa
from ostorlab.assets import ios_store
from ostorlab.assets import android_aab
from ostorlab.assets import android_apk
from ostorlab.assets import android_store
from ostorlab.assets import ip
from ostorlab.assets import domain_name
from ostorlab.assets import asset as base_asset

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


class AssetTypeEnum(enum.Enum):
    """Enum for the asset types."""

    ANDROID_FILE = "ANDROID_FILE"
    IOS_FILE = "IOS_FILE"
    ANDROID_STORE = "ANDROID_STORE"
    IOS_STORE = "IOS_STORE"
    LINK = "LINK"
    IP = "IP"
    DOMAIN = "DOMAIN"
    FILE = "FILE"


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
    created_time = sqlalchemy.Column(sqlalchemy.DateTime)
    progress = sqlalchemy.Column(sqlalchemy.Enum(ScanProgress))
    agent_group_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("agent_group.id")
    )

    @staticmethod
    def create(
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
        value: Optional[Union[bytes, int, float, str, bool, list, dict]] = None,
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
            value=value
            if isinstance(value, bytes) is True or value is None
            else AgentArgument.to_bytes(type, value),
        )
        with Database() as session:
            session.add(agent_argument)
            session.commit()
            return agent_argument

    @staticmethod
    def to_bytes(
        type: str, value: Optional[Union[int, float, str, bool, List, Dict]]
    ) -> bytes:
        """Convert the value to bytes."""
        if type == "string":
            return value.encode(encoding="utf-8")
        elif type in ("boolean", "bool"):
            return (1 if value is True else 0).to_bytes(1, byteorder="big")
        elif type == "number":
            return struct.pack("d", value)
        elif type in ("array", "object"):
            return json.dumps(value).encode(encoding="utf-8")
        else:
            raise NotImplementedError(f"Type {type} not supported")

    @staticmethod
    def from_bytes(type: str, value: bytes) -> Any:
        """Get the value of the argument."""
        if value is None:
            return None

        if type == "string":
            return value.decode(encoding="utf-8")
        elif type in ("boolean", "bool"):
            return bool(int.from_bytes(value, byteorder="big"))
        elif type == "number":
            return struct.unpack("d", value)[0]
        elif type in ("array", "object"):
            return json.loads(value.decode())
        else:
            return value


class AssetType(Base):
    """The Asset Type model"""

    __tablename__ = "asset_type"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    type = sqlalchemy.Column(sqlalchemy.Enum(AssetTypeEnum))

    asset_agent_groups = orm.relationship(
        "AgentGroup", secondary="agent_group_asset_type", back_populates="asset_types"
    )

    @staticmethod
    def create(type: AssetTypeEnum) -> "AssetType":
        """Persist the asset type in the database.

        Args:
            type: Asset type.
        Returns:
            AssetType object.
        """
        asset_type = AssetType(type=type)
        with Database() as session:
            session.add(asset_type)
            session.commit()
            return asset_type


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

    asset_types = orm.relationship(
        "AssetType",
        secondary="agent_group_asset_type",
        back_populates="asset_agent_groups",
    )

    @staticmethod
    def create(
        description: str,
        agents: Any,
        name: Optional[str] = None,
        asset_types: List[AssetTypeEnum] = [],
    ) -> "AgentGroup":
        """Persist the agent group in the database.

        Args:
            name: Agent group name.
            description: Agent group description.
            asset_types: List of asset types.
            agents: List of agents.
        Returns:
            AgentGroup object.
        """
        created_asset_types = []
        with Database() as session:
            for asset_type in asset_types:
                asset_type_model = (
                    session.query(AssetType).filter_by(type=asset_type).first()
                )
                if asset_type_model is None:
                    asset_type_model = AssetType.create(type=asset_type)
                created_asset_types.append(asset_type_model)

            agent_group = AgentGroup(
                name=name,
                description=description,
                created_time=datetime.datetime.now(),
                asset_types=created_asset_types,
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

            session.add(agent_group)
            session.commit()
            return agent_group

    @staticmethod
    def create_from_agent_group_definition(
        agent_group_definition: definitions.AgentGroupDefinition,
        asset_types: list[AssetTypeEnum] = [],
    ) -> "AgentGroup":
        """Create an agent group from an agent group definition.

        Args:
            agent_group_definition: Agent group definition.
        """
        agents = []
        for agent in agent_group_definition.agents:
            created_agent = Agent.create(key=agent.key)
            for arg in agent.args:
                AgentArgument.create(
                    name=arg.name,
                    type=arg.type,
                    value=arg.value,
                    description=arg.description,
                    agent_id=created_agent.id,
                )

            agents.append(created_agent)

        with Database() as session:
            agent_group = AgentGroup(
                name=agent_group_definition.name,
                description=agent_group_definition.description,
                agents=agents,
            )

            ag_asset_types = []
            for asset_type in asset_types:
                ag_asset_types.append(AssetType.create(type=asset_type))

            agent_group.asset_types = ag_asset_types
            session.add(agent_group)
            session.commit()
            return agent_group

    @staticmethod
    def create_from_directory(agent_groups_path: pathlib.Path) -> List["AgentGroup"]:
        """Create agent groups from a directory.

        Args:
            agent_groups_path: Path to the agent groups folder.

        Returns:
            List of agent groups.
        """
        with Database() as session:
            agent_groups = []
            for agent_group_file in agent_groups_path.iterdir():
                if (
                    agent_group_file.is_file() is True
                    and agent_group_file.suffix == ".yaml"
                ):
                    with open(agent_group_file, "r") as file:
                        agent_group_definition = (
                            definitions.AgentGroupDefinition.from_yaml(file)
                        )
                        count_agent_group = (
                            session.query(AgentGroup)
                            .filter_by(
                                name=agent_group_definition.name,
                            )
                            .count()
                        )
                        if count_agent_group > 0:
                            continue

                        file_name = agent_group_file.stem
                        asset_types = []
                        if file_name in ["network", "web", "autodiscovery"]:
                            asset_types = [
                                AssetTypeEnum.LINK,
                                AssetTypeEnum.IP,
                                AssetTypeEnum.DOMAIN,
                            ]
                        elif file_name == "sbom":
                            asset_types = [AssetTypeEnum.FILE]

                        agent_group = AgentGroup.create_from_agent_group_definition(
                            agent_group_definition=agent_group_definition,
                            asset_types=asset_types,
                        )
                        agent_groups.append(agent_group)
            return agent_groups


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


class AgentGroupAssetType(Base):
    """The Agent Group Asset Type model"""

    __tablename__ = "agent_group_asset_type"
    agent_group_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("agent_group.id"), primary_key=True
    )
    asset_type_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("asset_type.id"), primary_key=True
    )

    @staticmethod
    def create(agent_group_id: int, asset_type_id: int) -> "AgentGroupAssetType":
        """Persist the agent group asset type in the database.

        Args:
            agent_group_id: Agent group id.
            asset_type_id: Asset type id.
        Returns:
            AgentGroupAssetType object.
        """
        agent_group_asset_type = AgentGroupAssetType(
            agent_group_id=agent_group_id, asset_type_id=asset_type_id
        )
        with Database() as session:
            session.add(agent_group_asset_type)
            session.commit()
            return agent_group_asset_type


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

    @staticmethod
    def create_from_assets_definition(
        assets: Optional[List[base_asset.Asset]], scan_id: Optional[int] = None
    ) -> None:
        """Create the assets from the asset definition.

        Args:
            assets: The list of assets to create.
            scan_id: The scan id.
        """
        networks: List[Dict[str, Union[str, int]]] = []
        links: List[Dict[str, str]] = []
        domains: List[Dict[str, str]] = []
        for asset in assets:
            if (
                isinstance(asset, ip.IP)
                or isinstance(asset, ipv4.IPv4)
                or isinstance(asset, ipv6.IPv6)
            ):
                networks.append({"host": asset.host, "mask": asset.mask})
            elif isinstance(asset, link.Link):
                links.append({"url": asset.url, "method": asset.method})
            elif isinstance(asset, domain_name.DomainName):
                domains.append({"name": asset.name})
            elif isinstance(asset, ios_ipa.IOSIpa):
                IosFile.create(
                    path=asset.path,
                    scan_id=scan_id,
                    bundle_id=utils.get_bundle_id(asset.path),
                )
            elif isinstance(asset, ios_store.IOSStore):
                IosStore.create(bundle_id=asset.bundle_id, scan_id=scan_id)
            elif isinstance(asset, android_aab.AndroidAab) or isinstance(
                asset, android_apk.AndroidApk
            ):
                AndroidFile.create(
                    path=asset.path,
                    scan_id=scan_id,
                    package_name=utils.get_package_name(asset.path),
                )
            elif isinstance(asset, android_store.AndroidStore):
                AndroidStore.create(package_name=asset.package_name, scan_id=scan_id)

        if len(networks) > 0:
            Network.create(networks=networks, scan_id=scan_id)

        if len(links) > 0:
            Urls.create(links=links, scan_id=scan_id)

        if len(domains) > 0:
            DomainAsset.create(domains=domains, scan_id=scan_id)


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
    def create(
        package_name: str = "", path: str = "", scan_id: Optional[int] = None
    ) -> "AndroidFile":
        """Persist the android file information in the database.

        Args:
            package_name: The application identifier.
            path: Local/Remote path of the APK/AAB.
            scan_id: The scan id.

        Returns:
            android file object.
        """
        with Database() as session:
            asset = AndroidFile(
                package_name=package_name,
                path=path,
                scan_id=scan_id,
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
    def create(
        package_name: str = "",
        application_name: str = "",
        scan_id: Optional[int] = None,
    ) -> "AndroidStore":
        """Persist the android store information in the database.

        Args:
            package_name: The application identifier.
            application_name: The application name as shown in the store.
            scan_id: The scan id.

        Returns:
            android store object.
        """
        with Database() as session:
            asset = AndroidStore(
                package_name=package_name,
                application_name=application_name,
                scan_id=scan_id,
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
    def create(
        bundle_id: str = "", path: str = "", scan_id: Optional[int] = None
    ) -> "IosFile":
        """Persist the iOS file information in the database.

        Args:
            bundle_id: The application identifier.
            path: Local/Remote path of the IPA.
            scan_id: The scan id.

        Returns:
            iOS file object.
        """
        with Database() as session:
            asset = IosFile(
                bundle_id=bundle_id,
                path=path,
                scan_id=scan_id,
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
    def create(
        bundle_id: str = "", application_name: str = "", scan_id: Optional[int] = None
    ) -> "IosStore":
        """Persist the iOS store information in the database.

        Args:
            bundle_id: The application identifier.
            application_name: The application name as shown in the store.
            scan_id: The scan id.

        Returns:
            iOS store object.
        """
        with Database() as session:
            asset = IosStore(
                bundle_id=bundle_id,
                application_name=application_name,
                scan_id=scan_id,
            )
            session.add(asset)
            session.commit()
            return asset


class Link(Base):
    __tablename__ = "link"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    url = sqlalchemy.Column(sqlalchemy.String(4096))
    method = sqlalchemy.Column(sqlalchemy.String(8))
    urls_asset_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("urls.id")
    )

    @staticmethod
    def create(url: str, method: str, urls_asset_id: Optional[int] = None) -> "Link":
        """Persist the link information in the database.

        Args:
            url: The target URL.
            method: The HTTP method.
            urls_asset_id: The URL asset id.

        Returns:
            Link object.
        """
        with Database() as session:
            link = Link(url=url, method=method, urls_asset_id=urls_asset_id)
            session.add(link)
            session.commit()
            return link


class Urls(Asset):
    __tablename__ = "urls"
    id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("asset.id"), primary_key=True
    )

    __mapper_args__ = {
        "polymorphic_identity": "urls",
    }

    @staticmethod
    def create(links: List[dict[str, str]], scan_id: Optional[int] = None) -> "Urls":
        """Persist the URL information in the database.

        Args:
            links: list of the target URLs with methods.
            scan_id: The scan id.

        Returns:
            Urls object.
        """
        with Database() as session:
            urls_instance = Urls(scan_id=scan_id)
            session.add(urls_instance)
            session.commit()

            link_objects = [
                Link(
                    url=link.get("url"),
                    method=link.get("method", "GET"),
                    urls_asset_id=urls_instance.id,
                )
                for link in links
            ]
            session.add_all(link_objects)
            session.commit()
            return urls_instance

    @staticmethod
    def delete(urls_asset_id: int) -> None:
        """Delete the URL information from the database.

        Args:
            urls_asset_id: The URL id.
        """
        with Database() as session:
            session.query(Urls).filter_by(id=urls_asset_id).delete()
            session.query(Link).filter_by(urls_asset_id=urls_asset_id).delete()
            session.commit()


class IPRange(Base):
    __tablename__ = "ip"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    host = sqlalchemy.Column(sqlalchemy.String(50))
    mask = sqlalchemy.Column(sqlalchemy.String(50))
    network_asset_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("network.id")
    )

    @staticmethod
    def create(
        host: str, mask: str, network_asset_id: Optional[int] = None
    ) -> "IPRange":
        """Persist the IP information in the database.

        Args:
            host: The target IP address.
            mask: The subnet mask.
            network_asset_id: The network id.

        Returns:
            IP object.
        """
        with Database() as session:
            ip = IPRange(host=host, mask=mask, network_asset_id=network_asset_id)
            session.add(ip)
            session.commit()
            return ip


class Network(Asset):
    __tablename__ = "network"
    id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("asset.id"), primary_key=True
    )

    __mapper_args__ = {
        "polymorphic_identity": "network",
    }

    @staticmethod
    def create(
        networks: List[Dict[str, Union[str, int]]], scan_id: Optional[int] = None
    ) -> "Network":
        """Persist the Network information in the database.

        Args:
            networks: list of the target IP/range addresses.
            scan_id: The scan id.

        Returns:
            Network object.
        """
        with Database() as session:
            network_instance = Network(scan_id=scan_id)
            session.add(network_instance)
            session.commit()

            network_items = [
                IPRange(
                    host=network.get("host"),
                    mask=network.get(
                        "mask", str(ipaddress.ip_network(network.get("host")).prefixlen)
                    ),
                    network_asset_id=network_instance.id,
                )
                for network in networks
            ]
            session.add_all(network_items)
            session.commit()
            return network_instance

    @staticmethod
    def delete(network_id: int) -> None:
        """Delete the Network information from the database.

        Args:
            network_id: The network id.
        """
        with Database() as session:
            session.query(Network).filter_by(id=network_id).delete()
            session.query(IPRange).filter_by(network_asset_id=network_id).delete()
            session.commit()


class DomainName(Base):
    __tablename__ = "domain_name"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String(255))
    domain_asset_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("domain_asset.id")
    )

    @staticmethod
    def create(name: str, domain_asset_id: Optional[int] = None) -> "DomainName":
        """Persist the domain name information in the database.

        Args:
            name: The domain name.
            domain_asset_id: The domain asset id.

        Returns:
            DomainName object.
        """
        with Database() as session:
            domain_name = DomainName(name=name, domain_asset_id=domain_asset_id)
            session.add(domain_name)
            session.commit()
            return domain_name


class DomainAsset(Asset):
    __tablename__ = "domain_asset"
    id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("asset.id"), primary_key=True
    )

    __mapper_args__ = {
        "polymorphic_identity": "domain_asset",
    }

    @staticmethod
    def create(
        domains: List[Dict[str, str]], scan_id: Optional[int] = None
    ) -> "DomainAsset":
        """Persist the domain asset information in the database.

        Args:
            domains: list of domain names.
            scan_id: The scan id.

        Returns:
            DomainAsset object.
        """
        with Database() as session:
            domain_asset_instance = DomainAsset(scan_id=scan_id)
            session.add(domain_asset_instance)
            session.commit()

            for domain in domains:
                DomainName.create(
                    name=domain.get("name"), domain_asset_id=domain_asset_instance.id
                )
            return domain_asset_instance

    @staticmethod
    def delete(domain_asset_id: int) -> None:
        """Delete the domain asset information from the database.

        Args:
            domain_asset_id: The domain asset id.
        """
        with Database() as session:
            session.query(DomainAsset).filter_by(id=domain_asset_id).delete()
            session.query(DomainName).filter_by(
                domain_asset_id=domain_asset_id
            ).delete()
            session.commit()
