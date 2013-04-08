import datetime
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Unicode
from sqlalchemy import Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

favorites_table = Table('favorites', Base.metadata,
    Column('user_fk', Integer, ForeignKey('users.uid')),
    Column('event_type_fk', Integer, ForeignKey('event_types.eid'))
)

class EventType(Base):
    __tablename__ = 'event_types'

    eid = Column(Integer, primary_key=True)
    description = Column(Unicode(255))

    def __init__(self, description):
        self.description = description

class Occurance(Base):
    __tablename__ = 'occurances'

    oid = Column(Integer, primary_key=True)
    recorded_by_id = Column(Integer, ForeignKey('users.uid'))
    event_type_id = Column(Integer, ForeignKey('event_types.eid'))
    time = Column(DateTime, default=datetime.datetime.utcnow)

    recorded_by = relationship("User", backref="observed_occurances")
    event_type = relationship(
        "EventType",
        backref="occurances",
        lazy='joined',
        uselist=False
    )

    def __init__(self, recorded_by, event_type):
        self.recorded_by = recorded_by
        self.event_type = event_type

class User(Base):
    __tablename__ = 'users'

    uid = Column(Integer, primary_key=True)
    user_id = Column(Unicode(255), unique=True)
    
    favorites = relationship("EventType",
                            secondary=favorites_table)

    def __init__(self, user_id):
        self.user_id = user_id

    def publicName():
        return self.user_id

