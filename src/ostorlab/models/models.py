import enum
import datetime
import logging

from sqlalchemy import Column, Integer, Enum, ForeignKey, Table, String, DateTime, MetaData
from sqlalchemy.orm import relationship, backref, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

from ostorlab import configuration_manager as config_manager
from ostorlab.cli import console as cli_console

logger = logging.getLogger(__name__)
console = cli_console.Console()

ENGINE_URL = f'sqlite:///{config_manager.OSTORLAB_PRIVATE_DIR}/ostorlab_db.sqlite'

metadata = MetaData()
Base = declarative_base(metadata=metadata)


class RiskRating(enum.Enum):
    high = 'High'
    medium = 'Medium'
    low = 'Low'
    potentially = 'Potentially'
    hardening = 'Hardening'
    secure = 'Secure'
    important = 'Important'
    info = 'Info'


class Database:

    def __init__(self):
        self.db_engine = create_engine(ENGINE_URL)
        self.db_session = None

    def session(self):
        if self.db_session is None:
            Session = sessionmaker(expire_on_commit=False)
            Session.configure(bind=self.db_engine)
            self.db_session = Session()
            return self.db_session
        else:
            return self.db_session

    def create_db_tables(self):
        try:
            with self.db_engine.begin() as conn:
                metadata.create_all(conn)
                logger.info("Tables created")
        except Exception as e:
            logger.error("Error occurred during Table creation with the error {}".format(e))


class Scan(Base):
    __tablename__ = "scan"
    id = Column(Integer, primary_key=True)
    title = Column(String(255))
    created_time = Column(DateTime)
    risk_rating = Column(Enum(RiskRating))

    @staticmethod
    def save(title: str = 'My scan'):
        scan = Scan(title=title, created_time=datetime.datetime.now(), modified_time=datetime.datetime.now(),
                    risk_rating='info')
        database = Database()
        database.session().add(scan)
        database.session().commit()
        return scan

