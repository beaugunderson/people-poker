from sqlalchemy import Table, Column, DateTime, Integer, String, MetaData, \
        ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    __table_args__ = {'useexisting': True}

    id = Column(Integer, primary_key=True)

    user_id = Column(String)
    user_guid = Column(String)
    user_name = Column(String)

    def __init__(self, user_id, user_guid, user_name):
        self.user_id = user_id
        self.user_guid = user_guid
        self.user_name = user_name

    def __repr__(self):
        return "<User('%s', '%s', '%s')>" % (self.user_id, self.user_guid,
                self.user_name)


class Device(Base):
    __tablename__ = 'devices'
    __table_args__ = {'useexisting': True}

    id = Column(Integer, primary_key=True)
    name = Column(String)
    mac_address = Column(String)

    user = relationship(User, backref=backref('devices'), order_by=id)
    user_id = Column(Integer, ForeignKey('users.id'))

    def __init__(self, name, mac_address):
        self.name = name
        self.mac_address = mac_address

    def __repr__(self):
        return "<Device('%s', '%s')>" % (self.name, self.mac_address)


class Status(Base):
    __tablename__ = 'statuses'
    __table_args__ = {'useexisting': True}

    id = Column(Integer, primary_key=True)
    provider = Column(String)
    status = Column(String)
    update_time = Column(DateTime)

    user = relationship(User, backref=backref('statuses'), order_by=id)
    user_id = Column(Integer, ForeignKey('users.id'))

    def __init__(self, name, update_time, status):
        self.provider = provider
        self.status = status
        self.update_time = update_time

    def __repr__(self):
        return "<Status('%s', '%s', '%s')>" % (self.provider, self.status,
                self.update_time)