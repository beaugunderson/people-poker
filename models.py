from json import JSONEncoder
from datetime import datetime

from sqlalchemy import func, Column, DateTime, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref, class_mapper


def to_dict(self):
    for col in class_mapper(self.__class__).mapped_table.c:
        yield (col.name, getattr(self, col.name))


Base = declarative_base()

Base.to_dict = to_dict
Base.__iter__ = lambda self: self.to_dict()


class ModelEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()

        if hasattr(o, '__json__'):
            return o.__json__()

        return super(ModelEncoder, self).default(o)


class User(Base):
    __tablename__ = 'users'
    __table_args__ = {'useexisting': True}

    def __json__(self):
        properties = {
            'id': self.id,
            'statuses': map(dict, self.statuses or []),
            'account': self.account,
            'guid': self.guid,
            'display_name': self.display_name,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'department': self.department,
            'email': self.email,
            'provider': self.provider,
            'last_modified': self.last_modified,
        }

        return properties

    id = Column(Integer, primary_key=True)

    account = Column(String(length=128))
    guid = Column(String(length=128))
    display_name = Column(String(length=128))
    first_name = Column(String(length=64))
    last_name = Column(String(length=64))
    department = Column(String(length=64))
    email = Column(String(length=128))
    provider = Column(String(length=64))
    last_modified = Column(DateTime, onupdate=func.current_timestamp())

    def __init__(self, account, guid, display_name, first_name, last_name,
            department, email, provider):
        self.account = account
        self.guid = guid
        self.display_name = display_name
        self.first_name = first_name
        self.last_name = last_name
        self.department = department
        self.email = email
        self.provider = provider

    def __repr__(self):
        return "<User(%s, '%s', '%s', '%s')>" % (self.id, self.account,
                self.display_name, self.guid)


class Device(Base):
    __tablename__ = 'devices'
    __table_args__ = {'useexisting': True}

    def __json__(self):
        return {
            'user': self.user,
            'name': self.name,
            'mac_address': self.mac_address,
            'last_modified': self.last_modified,
        }

    id = Column(Integer, primary_key=True)

    name = Column(String(length=64))
    mac_address = Column(String(length=32))
    last_modified = Column(DateTime, onupdate=func.current_timestamp())

    user = relationship(User, backref=backref('devices'), order_by=id)
    user_id = Column(Integer, ForeignKey('users.id'))

    def __init__(self, name, mac_address):
        self.name = name
        self.mac_address = mac_address

    def __repr__(self):
        return "<Device(%s, '%s', '%s')>" % (self.id, self.name,
                self.mac_address)


class Status(Base):
    __tablename__ = 'statuses'
    __table_args__ = {'useexisting': True}

    def __json__(self):
        properties = {
            'user': dict(self.user or []),
            'status': self.status,
            'provider': self.provider,
            'update_time': self.update_time,
        }

        return properties

    id = Column(Integer, primary_key=True)

    provider = Column(String(length=64))
    # XXX Rename to be less ambiguous
    status = Column(String(length=32))
    # XXX Rename to 'time'?
    update_time = Column(DateTime, onupdate=func.current_timestamp())

    user = relationship(User, backref=backref('statuses'), order_by=id)
    user_id = Column(Integer, ForeignKey('users.id'))

    def __init__(self, provider, status, update_time):
        self.provider = provider
        self.status = status
        self.update_time = update_time

    def __repr__(self):
        return "<Status(%s, '%s', '%s', '%s')>" % (self.id, self.provider,
                self.status, self.update_time)
