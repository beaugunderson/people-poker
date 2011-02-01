from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy.orm import backref, relationship

from models.user import User
from models import Base


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
