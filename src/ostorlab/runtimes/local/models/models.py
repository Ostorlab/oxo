"""models contain the database engine logic and all the db models and the related operations"""

import enum
import datetime
import logging

import sqlalchemy
from sqlalchemy import orm
from sqlalchemy.ext import declarative

from ostorlab import configuration_manager as config_manager
from ostorlab.cli import console as cli_console

logger = logging.getLogger(__name__)
console = cli_console.Console()

ENGINE_URL = f'sqlite:///{config_manager.OSTORLAB_PRIVATE_DIR}/db.sqlite'

metadata = sqlalchemy.MetaData()
Base = declarative.declarative_base(metadata=metadata)


class RiskRating(enum.Enum):
    """Enumeration of the risk rating of a scan."""
    HIGH = 'High'
    MEDIUM = 'Medium'
    LOW = 'Low'
    POTENTIALLY = 'Potentially'
    HARDENING = 'Hardening'
    SECURE = 'Secure'
    IMPORTANT = 'Important'
    INFO = 'Info'


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
    created_time = sqlalchemy.Column(sqlalchemy.DateTime)
    risk_rating = sqlalchemy.Column(sqlalchemy.Enum(RiskRating))
    progress = sqlalchemy.Column(sqlalchemy.Enum(ScanProgress))

    @staticmethod
    def create(title: str = ''):
        """Persist the scan in the database.

        Args:
            title: Scan title.
        Returns:
            Scan object.
        """
        scan = Scan(title=title, created_time=datetime.datetime.now(), risk_rating='INFO', progress='NOT_STARTED')
        database = Database()
        database.session.add(scan)
        database.session.commit()
        return scan

