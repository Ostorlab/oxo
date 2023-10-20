"""models contain the database engine logic and all the db models and the related operations."""

import datetime
import enum
import json
import logging
import pathlib
from typing import Any, Dict, List, Optional
import types

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

metadata = sqlalchemy.MetaData()
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
        self._db_engine = sqlalchemy.create_engine(ENGINE_URL)
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

    @staticmethod
    def create(asset, title: str = ""):
        """Persist the scan in the database.

        Args:
            title: Scan title.
        Returns:
            Scan object.
        """
        with Database() as session:
            scan = Scan(
                title=title,
                asset=asset,
                created_time=datetime.datetime.now(),
                progress="NOT_STARTED",
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
    scan_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("scan.id"))
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
        cvss_v3_vector: str,
        dna: str,
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
        references = Vulnerability._prepare_references_markdown(references)
        vuln_location = Vulnerability._prepare_vuln_location_markdown(location)
        vuln = Vulnerability(
            scan_id=scan_id,
            title=title,
            short_description=short_description,
            description=description,
            recommendation=recommendation,
            references=references,
            technical_detail=technical_detail,
            risk_rating=risk_rating,
            cvss_v3_vector=cvss_v3_vector,
            dna=dna,
            location=vuln_location,
        )

        with Database() as session:
            session.add(vuln)
            session.commit()

        return vuln


class ScanStatus(Base):
    """The Scan model"""

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
