"""models contain the database engine logic and all the db models and the related operations"""

import enum
import datetime
import logging

from sqlalchemy import Column, Integer, Enum, String, DateTime, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

from ostorlab import configuration_manager as config_manager
from ostorlab.cli import console as cli_console

logger = logging.getLogger(__name__)
console = cli_console.Console()

ENGINE_URL = f'sqlite:///{config_manager.OSTORLAB_PRIVATE_DIR}/db.sqlite'

metadata = MetaData()
Base = declarative_base(metadata=metadata)


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


class Database:
    """Handles all Database instantiation and calls."""

    def __init__(self):
        """Constructs the database engine."""
        self._db_engine = create_engine(ENGINE_URL)
        self.db_session = None

    @property
    def session(self):
        """Session singleton to run queries on the db engine"""
        if self.db_session is None:
            session_maker = sessionmaker(expire_on_commit=False)
            session_maker.configure(bind=self._db_engine)
            self.db_session = session_maker()
            return self.db_session
        else:
            return self.db_session

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
    id = Column(Integer, primary_key=True)
    title = Column(String(255))
    created_time = Column(DateTime)
    risk_rating = Column(Enum(RiskRating))

    @staticmethod
    def save(title: str = 'My scan'):
        """Persist the scan in the database.

        Args:
            title: Scan title.
        Returns:
            Scan object.
        """
        scan = Scan(title=title, created_time=datetime.datetime.now(), risk_rating='info')
        database = Database()
        database.session.add(scan)
        database.session.commit()
        return scan

