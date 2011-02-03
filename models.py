from json import JSONEncoder

from sqlalchemy import Table, Column, DateTime, Integer, String, MetaData, \
        ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref

Base = declarative_base()


class ModelEncoder(JSONEncoder):
    def default(self, o):
        if hasattr(o, '__json__'):
            return o.__json__()

        return super(ModelEncoder, self).default(o)


class User(Base):
    __tablename__ = 'users'
    __table_args__ = {'useexisting': True}

    def __json__(self):
        return {
            'id': self.id,
            'account': self.account,
            'guid': self.guid,
            'display_name': self.display_name,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'department': self.department,
            'email': self.email,
        }

    id = Column(Integer, primary_key=True)

    account = Column(String(length=128))
    guid = Column(String(length=128))
    display_name = Column(String(length=128))
    first_name = Column(String(length=64))
    last_name = Column(String(length=64))
    department = Column(String(length=64))
    email = Column(String(length=128))

    def __init__(self, account, guid, display_name, first_name, last_name,
            department, email):
        self.account = account
        self.guid = guid
        self.display_name = display_name
        self.first_name = first_name
        self.last_name = last_name
        self.department = department
        self.email = email

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
        }

    id = Column(Integer, primary_key=True)
    name = Column(String(length=64))
    mac_address = Column(String(length=32))

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
        return {
            'user': self.user,
            'status': self.status,
            'provider': self.provider,
            'update_time': self.update_time.isoformat(),
        }

    id = Column(Integer, primary_key=True)
    provider = Column(String(length=64))
    status = Column(String(length=32))
    update_time = Column(DateTime)

    user = relationship(User, backref=backref('statuses'), order_by=id)
    user_id = Column(Integer, ForeignKey('users.id'))

    def __init__(self, provider, status, update_time):
        self.provider = provider
        self.status = status
        self.update_time = update_time

    def __repr__(self):
        return "<Status(%s, '%s', '%s', '%s')>" % (self.id, self.provider,
                self.status, self.update_time)
