"""models contain the database engine logic and all the db models and the related operations"""

import datetime
import enum
import logging

import sqlalchemy
from sqlalchemy import orm
from sqlalchemy.ext import declarative

from ostorlab import configuration_manager as config_manager
from ostorlab.cli import console as cli_console
from ostorlab.utils import risk_rating as utils_rik_rating

logger = logging.getLogger(__name__)
console = cli_console.Console()

ENGINE_URL = f'sqlite:///{config_manager.ConfigurationManager().conf_path}/db.sqlite'

metadata = sqlalchemy.MetaData()
Base = declarative.declarative_base(metadata=metadata)


class ScanProgress(enum.Enum):
    NOT_STARTED = 'not_started'
    IN_PROGRESS = 'in_progress'
    STOPPED = 'stopped'
    DONE = 'done'
    ERROR = 'error'


class Database:
    """Handles all Database instantiation and calls."""

    def __init__(self):
        """Constructs the database engine."""
        self._db_engine = sqlalchemy.create_engine(ENGINE_URL)
        self._db_session = None

    @property
    def session(self):
        """Session singleton to run queries on the db engine"""
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
            logger.info('Tables created')

    def drop_db_tables(self):
        """Drop the database tables."""
        metadata.drop_all(self._db_engine)
        logger.info('Tables dropped')


class Scan(Base):
    """The Scan model"""
    __tablename__ = 'scan'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    title = sqlalchemy.Column(sqlalchemy.String(255))
    asset = sqlalchemy.Column(sqlalchemy.String(255))
    created_time = sqlalchemy.Column(sqlalchemy.DateTime)
    progress = sqlalchemy.Column(sqlalchemy.Enum(ScanProgress))

    @staticmethod
    def create(asset, title: str = ''):
        """Persist the scan in the database.

        Args:
            title: Scan title.
        Returns:
            Scan object.
        """
        scan = Scan(title=title, asset=asset, created_time=datetime.datetime.now(), progress='NOT_STARTED')
        database = Database()
        database.session.add(scan)
        database.session.commit()
        return scan


class Vulnerability(Base):
    """The Vulnerability model"""
    __tablename__ = 'vulnerability'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    technical_detail = sqlalchemy.Column(sqlalchemy.Text)
    risk_rating = sqlalchemy.Column(sqlalchemy.Enum(utils_rik_rating.RiskRating))
    cvss_v3_vector = sqlalchemy.Column(sqlalchemy.String(1024))
    dna = sqlalchemy.Column(sqlalchemy.String(256))
    title = sqlalchemy.Column(sqlalchemy.String(256))
    short_description = sqlalchemy.Column(sqlalchemy.Text)
    description = sqlalchemy.Column(sqlalchemy.Text)
    recommendation = sqlalchemy.Column(sqlalchemy.Text)
    scan_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('scan.id'))

    @staticmethod
    def create(scan_id: int, title: str, short_description: str, description: str,
               recommendation: str, technical_detail: str, risk_rating: str,
               cvss_v3_vector: str, dna: str):
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
        Returns:
            Vulnerability object.
        """
        vuln = Vulnerability(
            scan_id=scan_id,
            title=title,
            short_description=short_description,
            description=description,
            recommendation=recommendation,
            technical_detail=technical_detail,
            risk_rating=risk_rating,
            cvss_v3_vector=cvss_v3_vector,
            dna=dna)
        database = Database()
        database.session.add(vuln)
        database.session.commit()
        return vuln


class ScanStatus(Base):
    """The Scan model"""
    __tablename__ = 'scan_status'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    created_time = sqlalchemy.Column(sqlalchemy.DateTime)
    key = sqlalchemy.Column(sqlalchemy.String(255))
    value = sqlalchemy.Column(sqlalchemy.Text)
    scan_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('scan.id'))

    @staticmethod
    def create(key: str, value: str, scan_id: int):
        """Persist the scan status in the database.

        Args:
            key: Scan status key.
            value: Scan status value.
        Returns:
            Scan status object.
        """
        scan_status = ScanStatus(key=key, created_time=datetime.datetime.now(), value=value, scan_id=scan_id)
        database = Database()
        database.session.add(scan_status)
        database.session.commit()
        return scan_status
